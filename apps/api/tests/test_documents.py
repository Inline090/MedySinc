import pymupdf
from httpx import AsyncClient

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
UPLOAD = "/api/v1/documents"

EMAIL = "dedupe@example.com"
PASSWORD = "secret123"


def _png(text: str) -> bytes:
    """Generates a PNG image containing the given text."""
    document = pymupdf.open()
    page = document.new_page(width=200, height=100)
    page.insert_text((20, 50), text, fontsize=16)
    data = page.get_pixmap(dpi=120).tobytes("png")
    document.close()

    return data


async def _sign_in(client: AsyncClient) -> None:
    """Registers and logs in a test user."""
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})


def _stub_ingestion(monkeypatch) -> None:
    """Disables the background ingestion process for testing."""

    async def noop(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr("app.controllers.documents.ingest_document", noop)


async def test_uploading_the_same_bytes_twice_is_rejected(client: AsyncClient, monkeypatch):
    """Checks that you cannot upload the exact same file twice."""
    _stub_ingestion(monkeypatch)
    await _sign_in(client)

    payload = _png("Paracetamol")

    first = await client.post(
        UPLOAD,
        files={"file": ("scan.png", payload, "image/png")},
    )
    second = await client.post(
        UPLOAD,
        files={"file": ("renamed.png", payload, "image/png")},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert "already uploaded" in second.json()["error"]["message"]


async def test_different_bytes_are_still_accepted(client: AsyncClient, monkeypatch):
    """Checks that different files can be uploaded without issue."""
    _stub_ingestion(monkeypatch)
    await _sign_in(client)

    first = await client.post(
        UPLOAD,
        files={"file": ("a.png", _png("Paracetamol"), "image/png")},
    )
    second = await client.post(
        UPLOAD,
        files={"file": ("b.png", _png("Ibuprofen"), "image/png")},
    )

    assert first.status_code == 201
    assert second.status_code == 201
