import pytest
from interactive_books.app.embed import EmbedBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.errors import BookError, BookErrorCode


class FakeBookRepository:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.books[book.id] = book

    def get(self, book_id: str) -> Book | None:
        return self.books.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self.books.values())

    def delete(self, book_id: str) -> None:
        self.books.pop(book_id, None)


class FakeChunkRepository:
    def __init__(self) -> None:
        self.chunks: dict[str, list[Chunk]] = {}

    def save_chunks(self, book_id: str, chunks: list[Chunk]) -> None:
        self.chunks[book_id] = chunks

    def get_by_book(self, book_id: str) -> list[Chunk]:
        return self.chunks.get(book_id, [])

    def get_up_to_page(self, book_id: str, page: int) -> list[Chunk]:
        return [c for c in self.get_by_book(book_id) if c.start_page <= page]

    def delete_by_book(self, book_id: str) -> None:
        self.chunks.pop(book_id, None)


class FakeEmbeddingProvider:
    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[0.1] * self._dimension for _ in texts]


class FailingEmbeddingProvider:
    @property
    def provider_name(self) -> str:
        return "failing"

    @property
    def dimension(self) -> int:
        return 4

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise BookError(BookErrorCode.EMBEDDING_FAILED, "API exploded")


class FakeEmbeddingRepository:
    def __init__(self) -> None:
        self.tables: set[str] = set()
        self.embeddings: dict[str, list[tuple[str, EmbeddingVector]]] = {}

    def ensure_table(self, provider_name: str, dimension: int) -> None:
        self.tables.add(f"{provider_name}_{dimension}")

    def save_embeddings(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        embeddings: list[EmbeddingVector],
    ) -> None:
        key = f"{provider_name}_{dimension}"
        if key not in self.embeddings:
            self.embeddings[key] = []
        self.embeddings[key].extend((book_id, ev) for ev in embeddings)

    def delete_by_book(self, provider_name: str, dimension: int, book_id: str) -> None:
        key = f"{provider_name}_{dimension}"
        if key in self.embeddings:
            self.embeddings[key] = [
                (bid, ev) for bid, ev in self.embeddings[key] if bid != book_id
            ]

    def has_embeddings(self, book_id: str, provider_name: str, dimension: int) -> bool:
        key = f"{provider_name}_{dimension}"
        return any(bid == book_id for bid, _ in self.embeddings.get(key, []))

    def search(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[str, float]]:
        return []

    def count_for_book(self, book_id: str, provider_name: str, dimension: int) -> int:
        key = f"{provider_name}_{dimension}"
        return sum(1 for bid, _ in self.embeddings.get(key, []) if bid == book_id)


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
            start_page=1,
            end_page=1,
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
