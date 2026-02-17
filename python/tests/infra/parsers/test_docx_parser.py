from pathlib import Path

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.docx import BookParser


class TestDocxParserMultiSection:
    def test_parse_splits_at_heading_boundaries(
        self, multi_section_docx: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_section_docx)
        # intro | Chapter One + content | Section 1.1 + content | Chapter Two + content
        assert len(pages) == 4

    def test_parse_assigns_sequential_page_numbers(
        self, multi_section_docx: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_section_docx)
        assert [p.page_number for p in pages] == [1, 2, 3, 4]

    def test_content_before_first_heading_is_page_one(
        self, multi_section_docx: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_section_docx)
        assert "Introduction text" in pages[0].text

    def test_heading_text_included_in_section(
        self, multi_section_docx: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_section_docx)
        assert "Chapter One" in pages[1].text
        assert "Chapter one content" in pages[1].text


class TestDocxParserNoHeadings:
    def test_no_headings_returns_single_page(self, docx_no_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(docx_no_headings)
        assert len(pages) == 1
        assert pages[0].page_number == 1

    def test_no_headings_contains_all_text(self, docx_no_headings: Path) -> None:
        parser = BookParser()
        pages = parser.parse(docx_no_headings)
        assert "First paragraph" in pages[0].text
        assert "Second paragraph" in pages[0].text


class TestDocxParserTables:
    def test_table_text_extracted(self, docx_with_tables: Path) -> None:
        parser = BookParser()
        pages = parser.parse(docx_with_tables)
        table_page = pages[-1]
        assert "Alice" in table_page.text
        assert "Bob" in table_page.text
        assert "30" in table_page.text


class TestDocxParserMixedContent:
    def test_mixed_content_splits_correctly(
        self, docx_mixed_content: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(docx_mixed_content)
        # intro | Section A + text + table | Section B + text
        assert len(pages) == 3

    def test_mixed_content_has_table_in_section(
        self, docx_mixed_content: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(docx_mixed_content)
        # Table is in Section A (page 2)
        assert "V1" in pages[1].text
        assert "V2" in pages[1].text


class TestDocxParserErrors:
    def test_empty_docx_raises_book_error(self, empty_docx: Path) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(empty_docx)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_file_not_found_raises_book_error(self) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.docx"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_invalid_docx_raises_book_error(self, invalid_docx: Path) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(invalid_docx)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
