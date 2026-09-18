from fastapi import APIRouter

from app.controllers.documents import (
    get_user_document,
    list_user_documents,
    upload_document,
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

router.post("", status_code=201)(upload_document)
router.get("")(list_user_documents)
router.get("/{document_id}")(get_user_document)
