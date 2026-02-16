from pathlib import Path

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.txt import PlainTextParser


class TestPlainTextParserShortFile:
    def test_short_file_produces_single_page(self, tmp_path: Path) -> None:
        path = tmp_path / "short.txt"
        path.write_text("Hello world. " * 100)  # ~1300 chars, under 3000
        parser = PlainTextParser()
        pages = parser.parse(path)
        assert len(pages) == 1
        assert pages[0].page_number == 1

    def test_short_file_contains_all_text(self, tmp_path: Path) -> None:
        text = "Hello world. " * 100
        path = tmp_path / "short.txt"
        path.write_text(text)
        parser = PlainTextParser()
        pages = parser.parse(path)
        assert pages[0].text == text


class TestPlainTextParserMultiPage:
    def test_multi_page_file_splits_by_chars_per_page(self, tmp_path: Path) -> None:
        path = tmp_path / "long.txt"
        path.write_text("x" * 7000)
        parser = PlainTextParser(chars_per_page=3000)
        pages = parser.parse(path)
        assert len(pages) == 3

    def test_page_numbers_are_sequential(self, tmp_path: Path) -> None:
        path = tmp_path / "long.txt"
        path.write_text("x" * 7000)
        parser = PlainTextParser(chars_per_page=3000)
        pages = parser.parse(path)
        assert [p.page_number for p in pages] == [1, 2, 3]

    def test_custom_chars_per_page(self, tmp_path: Path) -> None:
        path = tmp_path / "custom.txt"
        path.write_text("a" * 500)
        parser = PlainTextParser(chars_per_page=100)
        pages = parser.parse(path)
        assert len(pages) == 5


class TestPlainTextParserErrors:
    def test_empty_file_raises_book_error(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.txt"
        path.write_text("")
        parser = PlainTextParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(path)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_file_not_found_raises_book_error(self) -> None:
        parser = PlainTextParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.txt"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
