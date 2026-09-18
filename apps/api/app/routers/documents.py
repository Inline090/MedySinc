from fastapi import APIRouter

from app.controllers.documents import upload_document

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

router.post("", status_code=201)(upload_document)
