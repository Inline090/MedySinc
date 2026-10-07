from uuid import UUID

from httpx import AsyncClient

from app.ai.medicines import extract_medicines

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
MEDICATIONS = "/api/v1/medications"

EMAIL = "meds@example.com"
PASSWORD = "secret123"

# A small prescription, standing in for real extracted text.
SOURCE = "Rx\nDolo 650 - twice daily after meals\nHospital: City Hospital\nDr A. Rao"


class _FakeLLM:
    """A fake LLM that always returns the same answer and counts calls."""

    def __init__(self, reply: str) -> None:
        """Sets the canned reply."""
        self.reply = reply
        self.calls = 0

    async def complete(self, system_instruction: str, prompt: str) -> str:
        """Counts the call and returns the canned reply."""
        self.calls += 1
        return self.reply


async def test_a_field_the_document_never_stated_is_dropped(monkeypatch):
    """Checks that invented medicine details are thrown away."""

    reply = (
        '[{"medicine": "Dolo 650", "dose": "2 tablets",'
        ' "frequency": "twice daily after meals", "prescribed_on": null,'
        ' "hospital": "City Hospital", "notes": null}]'
    )
    llm = _FakeLLM(reply)

    monkeypatch.setattr("app.ai.medicines.get_llm", lambda: llm)

    rows = await extract_medicines(SOURCE)

    assert len(rows) == 1
    assert rows[0]["medicine"] == "Dolo 650"
    assert rows[0]["dose"] is None
    assert rows[0]["frequency"] == "twice daily after meals"
    assert rows[0]["hospital"] == "City Hospital"
    assert rows[0]["prescribed_on"] is None
    assert llm.calls == 1


async def test_a_medicine_the_document_never_listed_is_dropped(monkeypatch):
    """Checks that entire rows are dropped if the medicine name is made up."""

    # Only the medicine name, so this also covers a model that leaves the other keys out.
    llm = _FakeLLM('[{"medicine": "Paracetamol 500"}]')

    monkeypatch.setattr("app.ai.medicines.get_llm", lambda: llm)

    assert await extract_medicines(SOURCE) == []


async def test_a_reply_that_is_not_json_yields_nothing(monkeypatch):
    """Checks that invalid JSON from the model doesn't crash the app."""

    monkeypatch.setattr("app.ai.medicines.get_llm", lambda: _FakeLLM("Dolo 650, twice a day."))

    assert await extract_medicines(SOURCE) == []


async def test_empty_document_text_never_calls_the_model(monkeypatch):
    """Checks that we skip the LLM call entirely if there's no text to process."""

    llm = _FakeLLM("[]")

    monkeypatch.setattr("app.ai.medicines.get_llm", lambda: llm)

    assert await extract_medicines("   ") == []
    assert llm.calls == 0


async def test_medications_requires_a_signed_in_user(client: AsyncClient):
    """Checks that the medications endpoint requires a logged-in user."""

    response = await client.get(MEDICATIONS)

    assert response.status_code == 401


async def test_the_medications_list_is_empty_before_anything_is_extracted(
    client: AsyncClient,
):
    """Checks that a new user gets an empty medications list, not an error."""

    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    response = await client.get(MEDICATIONS)
    body = response.json()

    assert response.status_code == 200
    assert body["medicines"] == []
    assert body["total"] == 0


async def test_medicines_come_back_with_their_document(client: AsyncClient):
    """Checks that medicines are returned with the title of their source document."""

    from app.db.session import get_pool

    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    pool = get_pool()
    user_id = await pool.fetchval("SELECT id FROM users WHERE email = $1", EMAIL)

    document_id = await pool.fetchval(
        """
        INSERT INTO documents (
            user_id, title, original_name, storage_key,
            mime_type, size_bytes, processing_status
        )
        VALUES ($1, 'Prescription - Fever', 'rx.pdf', 'key',
                'application/pdf', 10, 'processed')
        RETURNING id
        """,
        user_id,
    )

    await pool.execute(
        """
        INSERT INTO document_medicines (
            document_id, user_id, hospital, medicine,
            dose, frequency, prescribed_on, notes
        )
        VALUES ($1, $2, 'City Hospital', 'Dolo 650',
                NULL, 'twice daily', '12/3/26', 'after meals')
        """,
        document_id,
        user_id,
    )

    body = (await client.get(MEDICATIONS)).json()

    assert body["total"] == 1

    medicine = body["medicines"][0]

    assert isinstance(UUID(medicine["id"]), UUID)
    assert medicine["medicine"] == "Dolo 650"
    assert medicine["frequency"] == "twice daily"
    assert medicine["prescribed_on"] == "12/3/26"
    assert medicine["notes"] == "after meals"
    assert medicine["dose"] is None
    assert medicine["hospital"] == "City Hospital"
    assert medicine["document_title"] == "Prescription - Fever"
