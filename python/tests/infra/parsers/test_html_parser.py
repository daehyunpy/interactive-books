from pathlib import Path

import pytest

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.html import BookParser


class TestHtmlParserContent:
    def test_parse_returns_single_page(self, html_with_content: Path) -> None:
        parser = BookParser()
        pages = parser.parse(html_with_content)
        assert len(pages) == 1
        assert pages[0].page_number == 1

    def test_parse_extracts_body_text(self, html_with_content: Path) -> None:
        parser = BookParser()
        pages = parser.parse(html_with_content)
        assert "First paragraph." in pages[0].text
        assert "Second paragraph." in pages[0].text

    def test_parse_preserves_block_structure(self, html_with_content: Path) -> None:
        parser = BookParser()
        pages = parser.parse(html_with_content)
        assert "Title\n" in pages[0].text

    def test_parse_strips_tags(self, html_with_content: Path) -> None:
        parser = BookParser()
        pages = parser.parse(html_with_content)
        assert "<p>" not in pages[0].text
        assert "<h1>" not in pages[0].text


class TestHtmlParserEdgeCases:
    def test_parse_no_body_raises_book_error(self, html_no_body: Path) -> None:
        """Selectolax normalizes HTML without a body tag to an empty body."""
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(html_no_body)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_parse_invalid_html_raises_book_error(
        self, invalid_html: Path
    ) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(invalid_html)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED


class TestHtmlParserErrors:
    def test_parse_empty_body_raises_book_error(
        self, html_empty_body: Path
    ) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(html_empty_body)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_file_not_found_raises_book_error(self) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.html"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
