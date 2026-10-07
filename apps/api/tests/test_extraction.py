import pymupdf
import pytest

from app.ai.extraction import extract_text, needs_ocr
from app.core.config import settings
from app.core.exceptions import AppError

LONG_TEXT = "Haemoglobin 13.5 g/dL and total leucocyte count 7500 cells per microlitre"


def _png_with_text(text: str) -> bytes:
    """Generates a PNG image containing the given text."""
    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 100), text, fontsize=20)
    data = page.get_pixmap(dpi=200).tobytes("png")
    document.close()

    return data


def _pdf_with_text_layer(text: str) -> bytes:
    """Generates a PDF with searchable text."""
    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 100), text, fontsize=10)
    data = document.tobytes()
    document.close()

    return data


def _scanned_pdf(text: str, pages: int = 1) -> bytes:
    """Generates a PDF where the text is baked into an image (needs OCR)."""
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
    """Checks that short text triggers OCR because it's likely just noise."""
    assert needs_ocr("") is True
    assert needs_ocr("too short") is True
    assert needs_ocr("x" * 60) is False


def test_a_pdf_with_a_text_layer_is_read_without_running_ocr(monkeypatch):
    """Checks that PDFs with text layers bypass the slow OCR step."""

    def explode(*_args, **_kwargs):
        raise AssertionError("OCR should not run when a PDF has a text layer")

    monkeypatch.setattr("app.ai.extraction._ocr_pdf", explode)

    assert "Haemoglobin" in extract_text(_pdf_with_text_layer(LONG_TEXT), "application/pdf")


def test_ocr_disabled_returns_no_text_from_an_image(monkeypatch):
    """Checks that disabling OCR returns empty text for images."""
    monkeypatch.setattr(settings, "OCR_ENABLED", False)

    assert extract_text(_png_with_text("Paracetamol"), "image/png") == ""


def test_ocr_reads_text_out_of_an_image():
    """Checks that OCR correctly extracts text from an image."""
    assert "paracetamol" in extract_text(_png_with_text("Paracetamol"), "image/png").lower()


def test_ocr_reads_a_pdf_that_has_no_text_layer():
    """Checks that scanned PDFs (images inside PDF) are read via OCR."""
    assert "paracetamol" in extract_text(_scanned_pdf("Paracetamol"), "application/pdf").lower()


def test_a_scanned_pdf_over_the_page_limit_is_rejected_before_ocr(monkeypatch):
    """Checks that scanned PDFs over the page limit are blocked early."""
    monkeypatch.setattr(settings, "OCR_MAX_PAGES", 1)

    with pytest.raises(AppError):
        extract_text(_scanned_pdf("Paracetamol", pages=2), "application/pdf")


def test_an_unreadable_image_is_rejected_cleanly():
    """Checks that invalid image bytes return an error instead of crashing."""
    with pytest.raises(AppError):
        extract_text(b"not an image at all", "image/png")
