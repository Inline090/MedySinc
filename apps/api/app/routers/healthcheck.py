from fastapi import APIRouter

from app.controllers.healthcheck import health_check

router = APIRouter(prefix="/api/v1/healthcheck", tags=["healthcheck"])

router.get("")(health_check)
