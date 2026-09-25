import io

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError

from app.core.config import settings
from app.core.exceptions import AppError

MIN_TEXT_LENGTH = 50


def extract_text(data: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        text = _extract_pdf_text(data)

        if not needs_ocr(text):
            return text

        return _ocr_pdf(data)

    return _ocr_image(data)


def needs_ocr(text: str) -> bool:
    return len(text.strip()) < MIN_TEXT_LENGTH


def _ocr(data: bytes) -> str:
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    try:
        return pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    except TesseractNotFoundError as error:
        raise AppError("The OCR engine is not installed on the server", 503) from error


def _ocr_image(data: bytes) -> str:
    if not settings.OCR_ENABLED:
        return ""

    return _ocr(data)


def _ocr_pdf(data: bytes) -> str:
    if not settings.OCR_ENABLED:
        return ""

    with pymupdf.open(stream=data, filetype="pdf") as document:
        if document.page_count > settings.OCR_MAX_PAGES:
            raise AppError(
                f"This looks like a scanned document of {document.page_count} pages, "
                f"which is over the {settings.OCR_MAX_PAGES} page OCR limit",
                422,
            )

        pages = [page.get_pixmap(dpi=settings.OCR_DPI).tobytes("png") for page in document]

    return "\n\n".join(_ocr(page) for page in pages)


def _extract_pdf_text(data: bytes) -> str:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            pages = [page.get_text().strip() for page in document]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as error:
        raise AppError("Could not read the uploaded PDF", 422) from error

    return "\n\n".join(page for page in pages if page)
