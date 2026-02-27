from unittest.mock import patch

import typer.testing
from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.main import app

runner = typer.testing.CliRunner()


def _ready_book(book_id: str = "book-1", title: str = "Test Book") -> Book:
    book = Book(id=book_id, title=title)
    book.start_ingestion()
    book.complete_ingestion()
    return book


def _sample_chunks() -> list[Chunk]:
    return [
        Chunk(
            id="c1",
            book_id="book-1",
            content="First chunk covering pages 1 through 3.",
            start_page=1,
            end_page=3,
            chunk_index=0,
        ),
        Chunk(
            id="c2",
            book_id="book-1",
            content="Second chunk covering pages 3 through 5.",
            start_page=3,
            end_page=5,
            chunk_index=1,
        ),
    ]


class TestSearchPageCommand:
    def test_displays_overlapping_chunks(self) -> None:
        book = _ready_book()

        with (
            patch("interactive_books.main._open_db"),
            patch(
                "interactive_books.infra.storage.book_repo.BookRepository"
            ) as mock_br_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
        ):
            mock_br_cls.return_value.get.return_value = book
            mock_cr_cls.return_value.get_by_page_range.return_value = _sample_chunks()

            result = runner.invoke(app, ["search-page", "book-1", "3"])

        assert result.exit_code == 0
        assert "2 chunk(s)" in result.output
        assert "pages 1-3" in result.output
        assert "pages 3-5" in result.output

    def test_no_content_message_when_empty(self) -> None:
        book = _ready_book()

        with (
            patch("interactive_books.main._open_db"),
            patch(
                "interactive_books.infra.storage.book_repo.BookRepository"
            ) as mock_br_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
        ):
            mock_br_cls.return_value.get.return_value = book
            mock_cr_cls.return_value.get_by_page_range.return_value = []

            result = runner.invoke(app, ["search-page", "book-1", "99"])

        assert "No content found on page 99" in result.output

    def test_book_not_found_error(self) -> None:
        with (
            patch("interactive_books.main._open_db"),
            patch(
                "interactive_books.infra.storage.book_repo.BookRepository"
            ) as mock_br_cls,
            patch("interactive_books.infra.storage.chunk_repo.ChunkRepository"),
        ):
            mock_br_cls.return_value.get.return_value = None

            result = runner.invoke(app, ["search-page", "nonexistent", "1"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_calls_get_by_page_range_with_same_start_and_end(self) -> None:
        book = _ready_book()

        with (
            patch("interactive_books.main._open_db"),
            patch(
                "interactive_books.infra.storage.book_repo.BookRepository"
            ) as mock_br_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
        ):
            mock_br_cls.return_value.get.return_value = book
            mock_cr_cls.return_value.get_by_page_range.return_value = []

            runner.invoke(app, ["search-page", "book-1", "7"])

            mock_cr_cls.return_value.get_by_page_range.assert_called_once_with(
                "book-1", 7, 7
            )
