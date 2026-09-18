from fastapi import APIRouter

from app.controllers.auth import login_user, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

router.post("/register", status_code=201)(register_user)
router.post("/login")(login_user)
