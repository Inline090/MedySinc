import pymupdf

from app.core.exceptions import AppError

MIN_TEXT_LENGTH = 50


def extract_text(data: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return _extract_pdf_text(data)

    return ""


def needs_ocr(text: str) -> bool:
    return len(text.strip()) < MIN_TEXT_LENGTH


def _extract_pdf_text(data: bytes) -> str:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            pages = [page.get_text().strip() for page in document]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as error:
        raise AppError("Could not read the uploaded PDF", 422) from error

    return "\n\n".join(page for page in pages if page)
