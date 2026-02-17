from pathlib import Path

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.pdf import BookParser


class TestBookParserMultiPage:
    def test_parse_returns_one_page_content_per_page(
        self, multi_page_pdf: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_page_pdf)
        assert len(pages) == 3

    def test_parse_assigns_correct_page_numbers(self, multi_page_pdf: Path) -> None:
        parser = BookParser()
        pages = parser.parse(multi_page_pdf)
        assert [p.page_number for p in pages] == [1, 2, 3]

    def test_parse_extracts_text_content(self, multi_page_pdf: Path) -> None:
        parser = BookParser()
        pages = parser.parse(multi_page_pdf)
        for i, page in enumerate(pages, start=1):
            assert f"Content of page {i}." in page.text


class TestBookParserEmptyPages:
    def test_parse_includes_empty_page_with_empty_text(
        self, pdf_with_empty_page: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(pdf_with_empty_page)
        assert len(pages) == 3
        assert pages[1].text.strip() == ""

    def test_parse_non_empty_pages_have_text(self, pdf_with_empty_page: Path) -> None:
        parser = BookParser()
        pages = parser.parse(pdf_with_empty_page)
        assert "Page one" in pages[0].text
        assert "Page three" in pages[2].text


class TestBookParserErrors:
    def test_file_not_found_raises_book_error(self) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.pdf"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_invalid_pdf_raises_book_error(self, invalid_pdf: Path) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(invalid_pdf)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
