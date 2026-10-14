import pymupdf
import pytest

from app.ai.extraction import extract_text
from app.core.config import settings
from app.core.exceptions import AppError


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


def test_an_image_is_read_by_the_model_and_not_by_ocr(monkeypatch):
    """Images hold handwriting, so they must never reach the local OCR engine."""

    def explode(*_args, **_kwargs):
        raise AssertionError("an image should not be sent to the OCR engine")

    monkeypatch.setattr("app.ai.extraction._ocr_image", explode)
    monkeypatch.setattr("app.ai.extraction.read_image", lambda data, mime: "Dolo 650 mg")

    assert extract_text(_png_with_text("ignored"), "image/png") == "Dolo 650 mg"


def test_the_image_model_receives_the_file_type(monkeypatch):
    """The model is told what kind of image it is looking at."""

    seen = {}

    def remember(data, mime_type):
        seen["mime"] = mime_type
        return "text"

    monkeypatch.setattr("app.ai.extraction.read_image", remember)

    extract_text(_png_with_text("anything"), "image/jpeg")

    assert seen["mime"] == "image/jpeg"


def test_a_pdf_is_read_by_ocr(monkeypatch):
    """PDFs hold printed text, so they go through the OCR engine."""

    monkeypatch.setattr("app.ai.extraction._ocr_image", lambda data: "Paracetamol")

    assert (
        "paracetamol"
        in extract_text(_pdf_with_text_layer("Paracetamol"), "application/pdf").lower()
    )


def test_ocr_reads_a_pdf_that_has_no_text_layer():
    """Checks that scanned PDFs (images inside PDF) are read via OCR."""
    assert "paracetamol" in extract_text(_scanned_pdf("Paracetamol"), "application/pdf").lower()


def test_a_pdf_over_the_page_limit_is_rejected_before_ocr(monkeypatch):
    """Checks that PDFs over the page limit are blocked early."""
    monkeypatch.setattr(settings, "OCR_MAX_PAGES", 1)

    with pytest.raises(AppError):
        extract_text(_scanned_pdf("Paracetamol", pages=2), "application/pdf")


def test_ocr_disabled_returns_no_text(monkeypatch):
    """Disabling OCR leaves PDFs empty rather than crashing."""
    monkeypatch.setattr(settings, "OCR_ENABLED", False)

    assert extract_text(_scanned_pdf("Paracetamol"), "application/pdf") == ""


def test_an_unsupported_file_type_is_rejected():
    """Anything that is not a PDF or an image is refused."""

    with pytest.raises(AppError):
        extract_text(b"col, row", "text/csv")
