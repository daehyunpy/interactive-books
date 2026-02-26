"""Integration test: spoiler prevention with real 1984.pdf.

Exercises the full pipeline: PdfBookParser → TextChunker → real repos
(BookRepository, ChunkRepository, EmbeddingRepository) backed by an
in-memory SQLite database with sqlite-vec. The only fake is the
EmbeddingProvider (no network calls).

Proves that the page-filtering spoiler prevention works with real book
content — not synthetic data. When current_page is set, search results
never include chunks from pages beyond that position.
"""

import hashlib
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest
from interactive_books.app.embed import EmbedBookUseCase
from interactive_books.app.ingest import IngestBookUseCase
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.page_content import PageContent
from interactive_books.infra.chunkers.recursive import TextChunker
from interactive_books.infra.parsers.pdf import BookParser as PdfBookParser
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "shared" / "schema"
FIXTURE_DIR = Path(__file__).resolve().parents[3] / "shared" / "fixtures"
PDF_1984 = FIXTURE_DIR / "1984.pdf"
FAKE_PROVIDER = "fake"
FAKE_DIMENSION = 4


class HashEmbeddingProvider:
    """Produces varied but deterministic vectors by hashing text content.

    Unlike a constant-vector fake, this gives sqlite-vec real distance
    variation so search results span the full page range instead of
    being biased toward the last-inserted chunks.
    """

    def __init__(self, dimension: int = FAKE_DIMENSION) -> None:
        self._dimension = dimension

    @property
    def provider_name(self) -> str:
        return FAKE_PROVIDER

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def _hash_to_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest[: self._dimension]]


class _StubUrlParser:
    def parse_url(self, url: str) -> list[PageContent]:
        return [PageContent(page_number=1, text="stub")]


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


@pytest.fixture
def embedding_provider() -> HashEmbeddingProvider:
    return HashEmbeddingProvider()


def _make_pipeline(
    *,
    book_repo: BookRepository,
    chunk_repo: ChunkRepository,
    embedding_repo: EmbeddingRepository,
    embedding_provider: HashEmbeddingProvider,
) -> tuple[IngestBookUseCase, EmbedBookUseCase, SearchBooksUseCase]:
    pdf_parser = PdfBookParser()
    stub_parser = PdfBookParser()  # unused for .pdf, required by signature

    embed_use_case = EmbedBookUseCase(
        embedding_provider=embedding_provider,  # type: ignore[arg-type]
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embedding_repo=embedding_repo,
    )

    ingest_use_case = IngestBookUseCase(
        pdf_parser=pdf_parser,
        txt_parser=stub_parser,
        epub_parser=stub_parser,
        docx_parser=stub_parser,
        html_parser=stub_parser,
        md_parser=stub_parser,
        url_parser=_StubUrlParser(),  # type: ignore[arg-type]
        chunker=TextChunker(),
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embed_use_case=embed_use_case,
    )

    search_use_case = SearchBooksUseCase(
        embedding_provider=embedding_provider,  # type: ignore[arg-type]
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embedding_repo=embedding_repo,
    )

    return ingest_use_case, embed_use_case, search_use_case


@dataclass
class IngestionResult:
    book: Book
    chunks: list[Chunk]
    search: SearchBooksUseCase
    book_repo: BookRepository


@pytest.fixture
def ingested_1984(
    book_repo: BookRepository,
    chunk_repo: ChunkRepository,
    embedding_repo: EmbeddingRepository,
    embedding_provider: HashEmbeddingProvider,
) -> IngestionResult:
    """Ingest and embed 1984.pdf via the full pipeline."""
    ingest, _, search = _make_pipeline(
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    book, embed_error = ingest.execute(PDF_1984, "Nineteen Eighty-Four")
    assert embed_error is None
    # Re-read from DB: EmbedBookUseCase updates a separate Book instance,
    # so the returned book lacks embedding_provider/embedding_dimension.
    saved_book = book_repo.get(book.id)
    assert saved_book is not None
    chunks = chunk_repo.get_by_book(book.id)
    return IngestionResult(
        book=saved_book,
        chunks=chunks,
        search=search,
        book_repo=book_repo,
    )


class TestSpoilerPreventionIntegration:
    """Full pipeline: ingest 1984.pdf → embed → search with page filtering."""

    def test_ingest_1984_produces_chunks_spanning_multiple_pages(
        self, ingested_1984: IngestionResult
    ) -> None:
        chunks = ingested_1984.chunks

        assert len(chunks) > 50
        assert min(c.start_page for c in chunks) == 1
        assert max(c.start_page for c in chunks) > 200
        assert all(c.start_page >= 1 for c in chunks)
        assert all(c.end_page >= c.start_page for c in chunks)
        assert ingested_1984.book.status == BookStatus.READY

    def test_page_filter_excludes_chunks_beyond_current_page(
        self, ingested_1984: IngestionResult
    ) -> None:
        book = ingested_1984.book
        book.set_current_page(30)
        ingested_1984.book_repo.save(book)

        results = ingested_1984.search.execute(book.id, "Winston")

        assert len(results) > 0
        assert all(r.start_page <= 30 for r in results)

    def test_no_filtering_when_current_page_is_zero(
        self, ingested_1984: IngestionResult
    ) -> None:
        book = ingested_1984.book
        assert book.current_page == 0

        results = ingested_1984.search.execute(book.id, "Winston", top_k=20)

        assert len(results) > 0
        assert any(r.start_page > 100 for r in results)

    def test_page_filter_at_boundary_includes_boundary_page(
        self, ingested_1984: IngestionResult
    ) -> None:
        chunks = ingested_1984.chunks
        mid_pages = sorted({c.start_page for c in chunks})
        boundary_page = mid_pages[len(mid_pages) // 2]

        book = ingested_1984.book
        book.set_current_page(boundary_page)
        ingested_1984.book_repo.save(book)

        results = ingested_1984.search.execute(book.id, "Winston")

        assert len(results) > 0
        assert all(r.start_page <= boundary_page for r in results)

    def test_page_override_overrides_current_page(
        self, ingested_1984: IngestionResult
    ) -> None:
        book = ingested_1984.book
        assert book.current_page == 0

        results = ingested_1984.search.execute(
            book.id, "Winston", page_override=30
        )

        assert len(results) > 0
        assert all(r.start_page <= 30 for r in results)

    def test_late_book_content_has_high_page_numbers(
        self, ingested_1984: IngestionResult
    ) -> None:
        chunks = ingested_1984.chunks
        room_101_chunks = [
            c for c in chunks if "room 101" in c.content.lower()
        ]

        assert len(room_101_chunks) > 0
        assert all(c.start_page > 150 for c in room_101_chunks)
