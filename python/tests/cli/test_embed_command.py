from unittest.mock import patch

import typer.testing
from interactive_books.domain.book import Book
from interactive_books.main import app

runner = typer.testing.CliRunner()


def _embedded_book(book_id: str = "book-1", title: str = "Test Book") -> Book:
    book = Book(id=book_id, title=title)
    book.start_ingestion()
    book.complete_ingestion()
    book.embedding_provider = "openai"
    book.embedding_dimension = 1536
    return book


class TestEmbedOutput:
    def test_shows_chunk_count(self) -> None:
        book = _embedded_book()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.main._require_env", return_value="sk-test"),
            patch("interactive_books.app.embed.EmbedBookUseCase") as mock_embed_cls,
            patch("interactive_books.infra.embeddings.openai.EmbeddingProvider"),
            patch("interactive_books.infra.storage.book_repo.BookRepository"),
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
            patch("interactive_books.infra.storage.embedding_repo.EmbeddingRepository"),
        ):
            mock_embed_cls.return_value.execute.return_value = book
            mock_cr_cls.return_value.count_by_book.return_value = 42
            result = runner.invoke(app, ["embed", "book-1"])

        assert result.exit_code == 0
        assert "Chunks:      42" in result.output


class TestEmbedVerbose:
    def test_verbose_shows_chunk_count_and_provider(self) -> None:
        book = _embedded_book()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.main._require_env", return_value="sk-test"),
            patch("interactive_books.app.embed.EmbedBookUseCase") as mock_embed_cls,
            patch(
                "interactive_books.infra.embeddings.openai.EmbeddingProvider"
            ) as mock_prov_cls,
            patch("interactive_books.infra.storage.book_repo.BookRepository"),
            patch(
                "interactive_books.infra.storage.chunk_repo.ChunkRepository"
            ) as mock_cr_cls,
            patch("interactive_books.infra.storage.embedding_repo.EmbeddingRepository"),
        ):
            mock_prov_cls.return_value.provider_name = "openai"
            mock_prov_cls.return_value.dimension = 1536
            mock_embed_cls.return_value.execute.return_value = book
            mock_cr_cls.return_value.count_by_book.return_value = 10
            result = runner.invoke(app, ["--verbose", "embed", "book-1"])

        assert result.exit_code == 0
        assert "[verbose] 10 chunks to embed" in result.output
        assert "[verbose] Provider: openai, Dimension: 1536" in result.output
