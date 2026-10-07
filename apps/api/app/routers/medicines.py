"""Routes for medications."""

from fastapi import APIRouter

from app.controllers.medicines import list_user_medicines

router = APIRouter(prefix="/api/v1/medications", tags=["medications"])

router.get("")(list_user_medicines)
