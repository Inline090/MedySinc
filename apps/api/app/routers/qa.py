from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from app.ai.answers import answer_question
from app.middlewares.auth import get_current_user
from app.schemas.qa import AskRequest

router = APIRouter(prefix="/api/v1/ask", tags=["qa"])


async def ask(
    payload: AskRequest,
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
) -> dict[str, object]:
    return await answer_question(user_id=user["id"], question=payload.question)


router.post("")(ask)
