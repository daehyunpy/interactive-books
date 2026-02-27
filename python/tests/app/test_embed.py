import pytest
from interactive_books.app.embed import EmbedBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode
from tests.fakes import (
    FakeBookRepository,
    FakeChunkRepository,
    FakeEmbeddingProvider,
    FakeEmbeddingRepository,
)


class FailingEmbeddingProvider:
    @property
    def provider_name(self) -> str:
        return "failing"

    @property
    def dimension(self) -> int:
        return 4

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise BookError(BookErrorCode.EMBEDDING_FAILED, "API exploded")


def _ready_book(book_id: str = "book-1", title: str = "Test Book") -> Book:
    book = Book(id=book_id, title=title)
    book.start_ingestion()
    book.complete_ingestion()
    return book


def _chunks(book_id: str = "book-1", count: int = 3) -> list[Chunk]:
    return [
        Chunk(
            id=f"chunk-{i}",
            book_id=book_id,
            content=f"Content of chunk {i}.",
            start_page=i + 1,
            end_page=i + 1,
            chunk_index=i,
        )
        for i in range(count)
    ]


def _make_use_case(
    *,
    book_repo: FakeBookRepository | None = None,
    chunk_repo: FakeChunkRepository | None = None,
    embedding_provider: FakeEmbeddingProvider | FailingEmbeddingProvider | None = None,
    embedding_repo: FakeEmbeddingRepository | None = None,
    batch_size: int = 100,
) -> tuple[
    EmbedBookUseCase, FakeBookRepository, FakeChunkRepository, FakeEmbeddingRepository
]:
    br = book_repo or FakeBookRepository()
    cr = chunk_repo or FakeChunkRepository()
    ep = embedding_provider or FakeEmbeddingProvider()
    er = embedding_repo or FakeEmbeddingRepository()
    return (
        EmbedBookUseCase(
            embedding_provider=ep,
            book_repo=br,
            chunk_repo=cr,
            embedding_repo=er,
            batch_size=batch_size,
        ),
        br,
        cr,
        er,
    )


class TestEmbedSuccess:
    def test_successful_embed_returns_book_with_metadata(self) -> None:
        use_case, book_repo, chunk_repo, _ = _make_use_case()
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks())

        result = use_case.execute("book-1")

        assert result.embedding_provider == "fake"
        assert result.embedding_dimension == 4

    def test_successful_embed_stores_vectors(self) -> None:
        use_case, book_repo, chunk_repo, embedding_repo = _make_use_case()
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks(count=5))

        use_case.execute("book-1")

        assert embedding_repo.count_for_book("book-1", "fake", 4) == 5

    def test_book_status_remains_ready(self) -> None:
        use_case, book_repo, chunk_repo, _ = _make_use_case()
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks())

        result = use_case.execute("book-1")

        assert result.status == BookStatus.READY


class TestEmbedBookNotFound:
    def test_raises_not_found(self) -> None:
        use_case, _, _, _ = _make_use_case()

        with pytest.raises(BookError) as exc_info:
            use_case.execute("nonexistent")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestEmbedNoChunks:
    def test_raises_invalid_state(self) -> None:
        use_case, book_repo, _, _ = _make_use_case()
        book = _ready_book()
        book_repo.save(book)

        with pytest.raises(BookError) as exc_info:
            use_case.execute("book-1")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE


class TestEmbedBatching:
    def test_single_batch_for_small_book(self) -> None:
        provider = FakeEmbeddingProvider()
        use_case, book_repo, chunk_repo, _ = _make_use_case(
            embedding_provider=provider, batch_size=100
        )
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks(count=50))

        use_case.execute("book-1")

        assert provider.call_count == 1

    def test_multiple_batches_for_large_book(self) -> None:
        provider = FakeEmbeddingProvider()
        use_case, book_repo, chunk_repo, _ = _make_use_case(
            embedding_provider=provider, batch_size=100
        )
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks(count=250))

        use_case.execute("book-1")

        assert provider.call_count == 3


class TestReEmbed:
    def test_re_embed_deletes_old_embeddings(self) -> None:
        use_case, book_repo, chunk_repo, embedding_repo = _make_use_case()
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks(count=3))

        use_case.execute("book-1")
        assert embedding_repo.count_for_book("book-1", "fake", 4) == 3

        use_case.execute("book-1")
        assert embedding_repo.count_for_book("book-1", "fake", 4) == 3


class TestEmbedFailureCleanup:
    def test_api_failure_cleans_up_and_preserves_book_state(self) -> None:
        use_case, book_repo, chunk_repo, embedding_repo = _make_use_case(
            embedding_provider=FailingEmbeddingProvider()
        )
        book = _ready_book()
        book_repo.save(book)
        chunk_repo.save_chunks(book.id, _chunks())

        with pytest.raises(BookError) as exc_info:
            use_case.execute("book-1")
        assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

        saved_book = book_repo.get("book-1")
        assert saved_book is not None
        assert saved_book.embedding_provider is None
        assert saved_book.embedding_dimension is None
        assert not embedding_repo.has_embeddings("book-1", "failing", 4)


class TestEmbedPageRangePropagation:
    def test_page_ranges_propagated_from_chunks_to_embedding_vectors(self) -> None:
        use_case, book_repo, chunk_repo, embedding_repo = _make_use_case()
        book = _ready_book()
        book_repo.save(book)
        chunks = [
            Chunk(
                id="chunk-0",
                book_id="book-1",
                content="First section.",
                start_page=1,
                end_page=3,
                chunk_index=0,
            ),
            Chunk(
                id="chunk-1",
                book_id="book-1",
                content="Second section.",
                start_page=4,
                end_page=7,
                chunk_index=1,
            ),
        ]
        chunk_repo.save_chunks("book-1", chunks)

        use_case.execute("book-1")

        stored = embedding_repo.embeddings["fake_4"]
        assert len(stored) == 2
        _, ev0 = stored[0]
        _, ev1 = stored[1]
        assert ev0.start_page == 1
        assert ev0.end_page == 3
        assert ev1.start_page == 4
        assert ev1.end_page == 7
