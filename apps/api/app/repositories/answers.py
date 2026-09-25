import hashlib
import json
from uuid import UUID

import asyncpg

from app.db.session import get_pool


def question_fingerprint(question: str) -> str:
    normalized = " ".join(question.lower().split())

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def find_cached_answer(
    *,
    user_id: UUID,
    question: str,
    ttl_hours: int,
) -> asyncpg.Record | None:
    pool = get_pool()

    return await pool.fetchrow(
        """
        SELECT answer, sources, model
        FROM answer_cache
        WHERE user_id = $1
          AND question_hash = $2
          AND created_at > NOW() - make_interval(hours => $3::int)
        """,
        user_id,
        question_fingerprint(question),
        ttl_hours,
    )


async def save_answer(
    *,
    user_id: UUID,
    question: str,
    answer: str,
    sources: list[dict[str, object]],
    model: str | None,
) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO answer_cache (user_id, question_hash, question, answer, sources, model)
        VALUES ($1, $2, $3, $4, $5::jsonb, $6)
        ON CONFLICT (user_id, question_hash)
        DO UPDATE SET answer = EXCLUDED.answer,
                      sources = EXCLUDED.sources,
                      model = EXCLUDED.model,
                      created_at = NOW()
        """,
        user_id,
        question_fingerprint(question),
        question,
        answer,
        json.dumps(sources),
        model,
    )


async def clear_answers_for_user(user_id: UUID) -> None:
    pool = get_pool()

    await pool.execute("DELETE FROM answer_cache WHERE user_id = $1", user_id)
