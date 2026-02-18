"""Integration test: ingest → auto-embed pipeline with real SQLite.

Exercises the full pipeline: TxtBookParser → TextChunker → real repos
(BookRepository, ChunkRepository, EmbeddingRepository) backed by an
in-memory SQLite database with sqlite-vec. The only fake is the
EmbeddingProvider (no network calls).
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from interactive_books.app.embed import EmbedBookUseCase
from interactive_books.app.ingest import IngestBookUseCase
from interactive_books.domain.book import BookStatus
from interactive_books.domain.page_content import PageContent
from interactive_books.infra.chunkers.recursive import TextChunker
from interactive_books.infra.parsers.txt import BookParser as TxtBookParser
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "shared" / "schema"
FAKE_PROVIDER = "fake"
FAKE_DIMENSION = 4


class FakeEmbeddingProvider:
    """Returns deterministic vectors without calling any API."""

    def __init__(self, dimension: int = FAKE_DIMENSION) -> None:
        self._dimension = dimension
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return FAKE_PROVIDER

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[0.1] * self._dimension for _ in texts]


class FailingEmbeddingProvider:
    """Simulates an embedding API failure."""

    @property
    def provider_name(self) -> str:
        return "failing"

    @property
    def dimension(self) -> int:
        return FAKE_DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        msg = "API rate limit exceeded"
        raise RuntimeError(msg)


@pytest.fixture
def vec_db() -> Generator[Database]:
    database = Database(":memory:", enable_vec=True)
    database.run_migrations(SCHEMA_DIR)
    yield database
    database.close()


@pytest.fixture
def book_repo(vec_db: Database) -> BookRepository:
    return BookRepository(vec_db)


@pytest.fixture
def chunk_repo(vec_db: Database) -> ChunkRepository:
    return ChunkRepository(vec_db)


@pytest.fixture
def embedding_repo(vec_db: Database) -> EmbeddingRepository:
    return EmbeddingRepository(vec_db)


def _write_txt(tmp_path: Path, content: str) -> Path:
    """Write a .txt file and return its path."""
    p = tmp_path / "book.txt"
    p.write_text(content, encoding="utf-8")
    return p


class _StubUrlParser:
    def parse_url(self, url: str) -> list[PageContent]:
        return [PageContent(page_number=1, text="stub")]


def _make_ingest_use_case(
    *,
    book_repo: BookRepository,
    chunk_repo: ChunkRepository,
    embed_use_case: EmbedBookUseCase | None = None,
) -> IngestBookUseCase:
    return IngestBookUseCase(
        pdf_parser=TxtBookParser(),  # unused for .txt files, but required
        txt_parser=TxtBookParser(),
        epub_parser=TxtBookParser(),  # unused for .txt files, but required
        docx_parser=TxtBookParser(),  # unused for .txt files, but required
        html_parser=TxtBookParser(),  # unused for .txt files, but required
        md_parser=TxtBookParser(),  # unused for .txt files, but required
        url_parser=_StubUrlParser(),  # type: ignore[arg-type]
        chunker=TextChunker(),
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embed_use_case=embed_use_case,
    )


class TestIngestAutoEmbedIntegration:
    """Full pipeline: ingest .txt → chunk → persist → embed → verify in DB."""

    def test_ingest_with_auto_embed_stores_embeddings(
        self,
        tmp_path: Path,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        provider = FakeEmbeddingProvider()
        embed_use_case = EmbedBookUseCase(
            embedding_provider=provider,  # type: ignore[arg-type]
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embedding_repo=embedding_repo,
        )
        use_case = _make_ingest_use_case(
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embed_use_case=embed_use_case,
        )

        txt_file = _write_txt(tmp_path, "Chapter 1. " * 100)
        book, embed_error = use_case.execute(txt_file, "Integration Test Book")

        assert embed_error is None
        assert book.status == BookStatus.READY

        # Re-read from DB to see embed metadata (auto-embed updates a
        # separate Book instance loaded inside EmbedBookUseCase)
        saved_book = book_repo.get(book.id)
        assert saved_book is not None
        assert saved_book.embedding_provider == FAKE_PROVIDER
        assert saved_book.embedding_dimension == FAKE_DIMENSION

        # Verify chunks persisted in real DB
        chunks = chunk_repo.get_by_book(book.id)
        assert len(chunks) > 0

        # Verify embeddings persisted in real sqlite-vec table
        assert embedding_repo.has_embeddings(book.id, FAKE_PROVIDER, FAKE_DIMENSION)

        # Verify provider was actually called
        assert provider.call_count >= 1

    def test_ingest_without_embed_skips_embeddings(
        self,
        tmp_path: Path,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        use_case = _make_ingest_use_case(
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embed_use_case=None,
        )

        txt_file = _write_txt(tmp_path, "Some book content here.")
        book, embed_error = use_case.execute(txt_file, "No Embed Book")

        assert embed_error is None
        assert book.status == BookStatus.READY
        assert book.embedding_provider is None
        assert book.embedding_dimension is None

        # Chunks should exist
        chunks = chunk_repo.get_by_book(book.id)
        assert len(chunks) > 0

    def test_ingest_with_embed_failure_keeps_book_ready(
        self,
        tmp_path: Path,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        embed_use_case = EmbedBookUseCase(
            embedding_provider=FailingEmbeddingProvider(),  # type: ignore[arg-type]
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embedding_repo=embedding_repo,
        )
        use_case = _make_ingest_use_case(
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embed_use_case=embed_use_case,
        )

        txt_file = _write_txt(tmp_path, "Content that will fail to embed.")
        book, embed_error = use_case.execute(txt_file, "Failing Embed Book")

        assert embed_error is not None
        assert "rate limit" in str(embed_error).lower()

        # Book should still be READY despite embed failure
        assert book.status == BookStatus.READY

        # Chunks should exist
        chunks = chunk_repo.get_by_book(book.id)
        assert len(chunks) > 0

        # No embeddings should be stored
        assert not embedding_repo.has_embeddings(book.id, "failing", FAKE_DIMENSION)

    def test_ingest_then_re_embed_replaces_embeddings(
        self,
        tmp_path: Path,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        """Ingest without embed, then embed separately — simulates the manual workflow."""
        use_case = _make_ingest_use_case(
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embed_use_case=None,
        )

        txt_file = _write_txt(tmp_path, "Content to embed later. " * 50)
        book, _ = use_case.execute(txt_file, "Late Embed Book")
        assert book.embedding_provider is None

        # Now embed separately (simulates `cli embed <book-id>`)
        provider = FakeEmbeddingProvider()
        embed_use_case = EmbedBookUseCase(
            embedding_provider=provider,  # type: ignore[arg-type]
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embedding_repo=embedding_repo,
        )
        updated_book = embed_use_case.execute(book.id)

        assert updated_book.embedding_provider == FAKE_PROVIDER
        assert updated_book.embedding_dimension == FAKE_DIMENSION

        chunks = chunk_repo.get_by_book(book.id)
        assert len(chunks) > 0
        assert embedding_repo.has_embeddings(book.id, FAKE_PROVIDER, FAKE_DIMENSION)
