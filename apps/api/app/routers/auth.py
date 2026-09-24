from fastapi import APIRouter

from app.controllers.auth import (
    google_callback,
    google_start,
    login_user,
    logout_user,
    read_current_user,
    refresh_tokens,
    register_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

router.post("/register", status_code=201)(register_user)
router.post("/login")(login_user)
router.post("/refresh")(refresh_tokens)
router.post("/logout")(logout_user)
router.get("/me")(read_current_user)
router.get("/google/start")(google_start)
router.get("/google/callback")(google_callback)
