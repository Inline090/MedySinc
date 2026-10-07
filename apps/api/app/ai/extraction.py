"""Pulls text from uploaded files (PDFs or images)."""

import io
from functools import lru_cache

import numpy as np
import pymupdf
from paddleocr import PaddleOCR
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.exceptions import AppError

MIN_TEXT_LENGTH = 50


@lru_cache
def _engine() -> PaddleOCR:
    """Sets up the OCR (image-to-text) engine once and reuses it."""

    return PaddleOCR(
        lang=settings.OCR_LANGUAGE,
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


def extract_text(data: bytes, mime_type: str) -> str:
    """Gets the text from an uploaded file, using OCR only if needed."""

    if mime_type == "application/pdf":
        text = _extract_pdf_text(data)

        if not needs_ocr(text):
            return text

        return _ocr_pdf(data)

    return _ocr_image(data)


def needs_ocr(text: str) -> bool:
    """Checks if a PDF has so little text that we should try OCR instead."""

    return len(text.strip()) < MIN_TEXT_LENGTH


def _ocr_image(data: bytes) -> str:
    """Uses OCR to find text in an image."""

    if not settings.OCR_ENABLED:
        return ""

    try:
        image = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
    except (UnidentifiedImageError, OSError) as error:
        raise AppError("Could not read the uploaded image", 422) from error

    lines: list[str] = []

    for result in _engine().predict(image):
        lines.extend(result.get("rec_texts") or [])

    return "\n".join(lines)


def _ocr_pdf(data: bytes) -> str:
    """Turns a scanned PDF into images and runs OCR on each page."""

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

    return "\n\n".join(_ocr_image(page) for page in pages)


def _extract_pdf_text(data: bytes) -> str:
    """Reads the built-in text from a PDF. Fast and easy."""

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            pages = [page.get_text().strip() for page in document]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as error:
        raise AppError("Could not read the uploaded PDF", 422) from error

    return "\n\n".join(page for page in pages if page)
