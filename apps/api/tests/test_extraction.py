import shutil
from pathlib import Path

import pymupdf
import pytest

from app.ai.extraction import extract_text, needs_ocr
from app.core.config import settings
from app.core.exceptions import AppError

LONG_TEXT = "Haemoglobin 13.5 g/dL and total leucocyte count 7500 cells per microlitre"


def _tesseract_available() -> bool:
    if settings.TESSERACT_CMD:
        return Path(settings.TESSERACT_CMD).exists()

    return shutil.which("tesseract") is not None


requires_tesseract = pytest.mark.skipif(
    not _tesseract_available(),
    reason="the tesseract binary is not installed",
)


def _png_with_text(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 100), text, fontsize=20)
    data = page.get_pixmap(dpi=200).tobytes("png")
    document.close()

    return data


def _pdf_with_text_layer(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 100), text, fontsize=10)
    data = document.tobytes()
    document.close()

    return data


def _scanned_pdf(text: str, pages: int = 1) -> bytes:
    source = pymupdf.open()
    source_page = source.new_page(width=400, height=200)
    source_page.insert_text((40, 100), text, fontsize=20)
    image = source_page.get_pixmap(dpi=200).tobytes("png")
    source.close()

    target = pymupdf.open()

    for _ in range(pages):
        page = target.new_page(width=400, height=200)
        page.insert_image(page.rect, stream=image)

    data = target.tobytes()
    target.close()

    return data


def test_needs_ocr_flags_text_that_is_too_short_to_use():
    assert needs_ocr("") is True
    assert needs_ocr("too short") is True
    assert needs_ocr("x" * 60) is False


def test_a_pdf_with_a_text_layer_is_read_without_running_ocr(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("OCR should not run when a PDF has a text layer")

    monkeypatch.setattr("app.ai.extraction._ocr_pdf", explode)

    assert "Haemoglobin" in extract_text(_pdf_with_text_layer(LONG_TEXT), "application/pdf")


def test_ocr_disabled_returns_no_text_from_an_image(monkeypatch):
    monkeypatch.setattr(settings, "OCR_ENABLED", False)

    assert extract_text(_png_with_text("Paracetamol"), "image/png") == ""


@requires_tesseract
def test_ocr_reads_text_out_of_an_image():
    assert "paracetamol" in extract_text(_png_with_text("Paracetamol"), "image/png").lower()


@requires_tesseract
def test_ocr_reads_a_pdf_that_has_no_text_layer():
    assert "paracetamol" in extract_text(_scanned_pdf("Paracetamol"), "application/pdf").lower()


@requires_tesseract
def test_a_scanned_pdf_over_the_page_limit_is_rejected_before_ocr(monkeypatch):
    monkeypatch.setattr(settings, "OCR_MAX_PAGES", 1)

    with pytest.raises(AppError):
        extract_text(_scanned_pdf("Paracetamol", pages=2), "application/pdf")
