from fastapi import APIRouter

from app.controllers.documents import (
    delete_user_document,
    get_user_document,
    list_user_documents,
    summarize_user_document,
    upload_document,
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

router.post("", status_code=201)(upload_document)
router.get("")(list_user_documents)
router.get("/{document_id}")(get_user_document)
router.delete("/{document_id}")(delete_user_document)
router.post("/{document_id}/summary")(summarize_user_document)
