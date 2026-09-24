from fastapi import APIRouter, Depends

from app.controllers.documents import (
    delete_user_document,
    get_user_document,
    list_user_documents,
    summarize_user_document,
    upload_document,
)
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

router.post(
    "",
    status_code=201,
    dependencies=[Depends(rate_limit("documents:upload", 30))],
)(upload_document)

router.get("")(list_user_documents)
router.get("/{document_id}")(get_user_document)
router.delete("/{document_id}")(delete_user_document)
router.post("/{document_id}/summary")(summarize_user_document)
