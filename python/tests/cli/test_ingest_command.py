from pathlib import Path
from unittest.mock import patch

import typer.testing
from interactive_books.domain.book import Book
from interactive_books.main import app

runner = typer.testing.CliRunner()


def _ready_book(book_id: str = "book-1", title: str = "Test Book") -> Book:
    book = Book(id=book_id, title=title)
    book.start_ingestion()
    book.complete_ingestion()
    return book


def _ready_book_with_embeddings(
    book_id: str = "book-1", title: str = "Test Book"
) -> Book:
    book = _ready_book(book_id, title)
    book.embedding_provider = "openai"
    book.embedding_dimension = 1536
    return book


class TestIngestOutput:
    def test_shows_tip_when_no_api_key(self, tmp_path: Path) -> None:
        book = _ready_book()
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.app.ingest.IngestBookUseCase") as mock_ingest_cls,
            patch("interactive_books.infra.storage.chunk_repo.ChunkRepository"),
            patch.dict("os.environ", {}, clear=False),
        ):
            mock_ingest_cls.return_value.execute.return_value = (book, None)
            # Remove key if set
            import os

            os.environ.pop("OPENAI_API_KEY", None)
            result = runner.invoke(app, ["ingest", str(pdf)])

        assert result.exit_code == 0
        assert "Tip: Set OPENAI_API_KEY" in result.output

    def test_shows_embedded_on_success(self, tmp_path: Path) -> None:
        book = _ready_book_with_embeddings()
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.app.ingest.IngestBookUseCase") as mock_ingest_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
            patch("interactive_books.infra.embeddings.openai.EmbeddingProvider"),
            patch("interactive_books.infra.storage.embedding_repo.EmbeddingRepository"),
            patch("interactive_books.app.embed.EmbedBookUseCase"),
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False),
        ):
            mock_ingest_cls.return_value.execute.return_value = (book, None)
            mock_cr_cls.return_value.count_by_book.return_value = 5
            result = runner.invoke(app, ["ingest", str(pdf)])

        assert result.exit_code == 0
        assert "Embedded:    openai" in result.output

    def test_shows_warning_on_embed_failure(self, tmp_path: Path) -> None:
        book = _ready_book()
        embed_error = RuntimeError("API rate limit")
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.app.ingest.IngestBookUseCase") as mock_ingest_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
            patch("interactive_books.infra.embeddings.openai.EmbeddingProvider"),
            patch("interactive_books.infra.storage.embedding_repo.EmbeddingRepository"),
            patch("interactive_books.app.embed.EmbedBookUseCase"),
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False),
        ):
            mock_ingest_cls.return_value.execute.return_value = (book, embed_error)
            mock_cr_cls.return_value.count_by_book.return_value = 5
            result = runner.invoke(app, ["ingest", str(pdf)])

        assert result.exit_code == 0
        assert "Warning: Embedding failed" in result.output
        assert "Tip: Run 'embed' command separately" in result.output


class TestIngestVerbose:
    def test_verbose_shows_chunk_count(self, tmp_path: Path) -> None:
        book = _ready_book()
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.app.ingest.IngestBookUseCase") as mock_ingest_cls,
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
            patch.dict("os.environ", {}, clear=False),
        ):
            mock_ingest_cls.return_value.execute.return_value = (book, None)
            mock_cr_cls.return_value.count_by_book.return_value = 12
            import os

            os.environ.pop("OPENAI_API_KEY", None)
            result = runner.invoke(app, ["--verbose", "ingest", str(pdf)])

        assert result.exit_code == 0
        assert "[verbose] 12 chunks created" in result.output
