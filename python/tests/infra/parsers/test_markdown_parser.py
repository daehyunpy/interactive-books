from pathlib import Path

import pytest

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.markdown import BookParser


class TestMarkdownParserHeadings:
    def test_parse_splits_at_h1_headings(self, md_with_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        # Intro + Chapter One + Section 1.1 + Chapter Two = 4 pages
        assert len(pages) == 4

    def test_parse_splits_at_h2_headings(self, md_with_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        # Page 3 starts with "Section 1.1"
        assert "Section 1.1" in pages[2].text

    def test_parse_mixed_h1_h2_splits_correctly(
        self, md_with_headings: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        assert "Introduction" in pages[0].text
        assert "Chapter One" in pages[1].text
        assert "Section 1.1" in pages[2].text
        assert "Chapter Two" in pages[3].text

    def test_parse_assigns_sequential_page_numbers(
        self, md_with_headings: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        assert [p.page_number for p in pages] == [1, 2, 3, 4]

    def test_content_before_first_heading_is_page_one(
        self, md_with_headings: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        assert "Introduction before any heading." in pages[0].text

    def test_heading_text_included_in_section(
        self, md_with_headings: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        assert "Chapter One" in pages[1].text


class TestMarkdownParserFormatting:
    def test_parse_strips_formatting(self, md_with_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_headings)
        # Bold markers stripped
        assert "**" not in pages[1].text
        assert "bold" in pages[1].text
        # Italic markers stripped
        assert "*italic*" not in pages[2].text
        assert "italic" in pages[2].text
        # Link syntax stripped
        assert "[a link]" not in pages[2].text
        assert "a link" in pages[2].text
        # Inline code markers stripped
        assert "`code`" not in pages[3].text
        assert "code" in pages[3].text


class TestMarkdownParserEdgeCases:
    def test_no_headings_returns_single_page(self, md_no_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(md_no_headings)
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert "First paragraph" in pages[0].text

    def test_headings_in_code_blocks_ignored(
        self, md_with_code_block: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(md_with_code_block)
        # Only the real heading should split; code block headings are not page breaks
        assert len(pages) == 1
        assert "Real Heading" in pages[0].text


class TestMarkdownParserErrors:
    def test_empty_file_raises_book_error(self, md_empty: Path) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(md_empty)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_file_not_found_raises_book_error(self) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.md"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
