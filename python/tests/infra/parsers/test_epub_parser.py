from pathlib import Path

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.epub import BookParser


class TestEpubParserMultiChapter:
    def test_parse_returns_one_page_per_chapter(
        self, multi_chapter_epub: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_chapter_epub)
        assert len(pages) == 3

    def test_parse_assigns_sequential_page_numbers(
        self, multi_chapter_epub: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(multi_chapter_epub)
        assert [p.page_number for p in pages] == [1, 2, 3]

    def test_parse_extracts_chapter_text(self, multi_chapter_epub: Path) -> None:
        parser = BookParser()
        pages = parser.parse(multi_chapter_epub)
        for i, page in enumerate(pages, start=1):
            assert f"Chapter {i} content" in page.text


class TestEpubParserSingleChapter:
    def test_single_chapter_returns_one_page(
        self, single_chapter_epub: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(single_chapter_epub)
        assert len(pages) == 1
        assert pages[0].page_number == 1

    def test_single_chapter_contains_text(self, single_chapter_epub: Path) -> None:
        parser = BookParser()
        pages = parser.parse(single_chapter_epub)
        assert "Only chapter" in pages[0].text


class TestEpubParserWhitespaceChapter:
    def test_whitespace_chapter_included_with_empty_text(
        self, epub_with_whitespace_chapter: Path
    ) -> None:
        parser = BookParser()
        pages = parser.parse(epub_with_whitespace_chapter)
        assert len(pages) == 3
        assert pages[1].text.strip() == ""


class TestEpubParserDrmDetection:
    def test_drm_protected_epub_raises_drm_error(
        self, drm_protected_epub: Path
    ) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(drm_protected_epub)
        assert exc_info.value.code == BookErrorCode.DRM_PROTECTED


class TestEpubParserErrors:
    def test_file_not_found_raises_book_error(self) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(Path("/nonexistent/book.epub"))
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_invalid_zip_raises_book_error(self, invalid_epub: Path) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(invalid_epub)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_epub_with_no_chapters_raises_book_error(
        self, epub_with_no_chapters: Path
    ) -> None:
        parser = BookParser()
        with pytest.raises(BookError) as exc_info:
            parser.parse(epub_with_no_chapters)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED
