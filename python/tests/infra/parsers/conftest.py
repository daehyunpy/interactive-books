from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    """Create a 3-page PDF with known text content."""
    path = tmp_path / "multi_page.pdf"
    doc = pymupdf.open()
    for i in range(1, 4):
        page = doc.new_page()
        page.insert_text((72, 72), f"Content of page {i}.")
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def pdf_with_empty_page(tmp_path: Path) -> Path:
    """Create a 3-page PDF where page 2 has no text (simulates image-only page)."""
    path = tmp_path / "empty_page.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page one has text.")
    doc.new_page()  # page 2: blank
    page3 = doc.new_page()
    page3.insert_text((72, 72), "Page three has text.")
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def invalid_pdf(tmp_path: Path) -> Path:
    """Create a file with .pdf extension but invalid content."""
    path = tmp_path / "invalid.pdf"
    path.write_text("This is not a PDF file.")
    return path
