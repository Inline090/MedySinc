from fastapi import APIRouter, Depends

from app.controllers.auth import (
    google_callback,
    google_start,
    login_user,
    logout_user,
    read_current_user,
    refresh_tokens,
    register_user,
)
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

router.post(
    "/register",
    status_code=201,
    dependencies=[Depends(rate_limit("auth:register", 5))],
)(register_user)

router.post("/login", dependencies=[Depends(rate_limit("auth:login", 10))])(login_user)
router.post("/refresh")(refresh_tokens)
router.post("/logout")(logout_user)
router.get("/me")(read_current_user)
router.get("/google/start")(google_start)
router.get("/google/callback")(google_callback)
