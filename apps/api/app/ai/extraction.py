"""Pulls text from uploaded files (PDFs or images)."""

import io
from functools import lru_cache

import numpy as np
import pymupdf
from paddleocr import PaddleOCR
from PIL import Image, UnidentifiedImageError

from app.ai.llm import read_image
from app.core.config import settings
from app.core.exceptions import AppError

PDF_TYPE = "application/pdf"


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
    """Gets the text from an uploaded file.

    The two kinds of file hold different things. A PDF holds printed text, which
    PaddleOCR reads well. An image usually holds handwriting, which PaddleOCR
    reads badly, so images go to the vision model instead.
    """

    if mime_type == PDF_TYPE:
        return _ocr_pdf(data)

    if mime_type.startswith("image/"):
        return read_image(data, mime_type)

    raise AppError(f"Files of type {mime_type} are not supported", 415)


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
    """Turns a PDF into page images and runs OCR on each page."""

    if not settings.OCR_ENABLED:
        return ""

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if document.page_count > settings.OCR_MAX_PAGES:
                raise AppError(
                    f"This document has {document.page_count} pages, which is over "
                    f"the {settings.OCR_MAX_PAGES} page limit",
                    422,
                )

            pages = [page.get_pixmap(dpi=settings.OCR_DPI).tobytes("png") for page in document]
    except AppError:
        raise
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as error:
        raise AppError("Could not read the uploaded PDF", 422) from error

    return "\n\n".join(_ocr_image(page) for page in pages)
