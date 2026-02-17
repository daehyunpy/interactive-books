import pytest
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.search_result import SearchResult


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

    def count_by_book(self, book_id: str) -> int:
        return len(self.chunks.get(book_id, []))

    def delete_by_book(self, book_id: str) -> None:
        self.chunks.pop(book_id, None)


class FakeEmbeddingProvider:
    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension
        self.last_texts: list[str] = []

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.last_texts = texts
        return [[0.1] * self._dimension for _ in texts]


class FakeEmbeddingRepository:
    """Fake that returns pre-configured search results."""

    def __init__(self) -> None:
        self._search_results: list[tuple[str, float]] = []
        self.last_search_top_k: int | None = None

    def set_search_results(self, results: list[tuple[str, float]]) -> None:
        self._search_results = results

    def ensure_table(self, provider_name: str, dimension: int) -> None:
        pass

    def save_embeddings(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        embeddings: list[EmbeddingVector],
    ) -> None:
        pass

    def delete_by_book(self, provider_name: str, dimension: int, book_id: str) -> None:
        pass

    def has_embeddings(self, book_id: str, provider_name: str, dimension: int) -> bool:
        return False

    def search(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[str, float]]:
        self.last_search_top_k = top_k
        return self._search_results[:top_k]


def _ready_book_with_embeddings(book_id: str = "book-1", current_page: int = 0) -> Book:
    book = Book(id=book_id, title="Test Book")
    book.start_ingestion()
    book.complete_ingestion()
    book.embedding_provider = "fake"
    book.embedding_dimension = 4
    if current_page > 0:
        book.set_current_page(current_page)
    return book


def _chunks_with_pages(book_id: str = "book-1") -> list[Chunk]:
    """Create chunks spanning pages 1-100."""
    return [
        Chunk(
            id="c1",
            book_id=book_id,
            content="Early content",
            start_page=1,
            end_page=10,
            chunk_index=0,
        ),
        Chunk(
            id="c2",
            book_id=book_id,
            content="Mid content",
            start_page=40,
            end_page=50,
            chunk_index=1,
        ),
        Chunk(
            id="c3",
            book_id=book_id,
            content="Late content",
            start_page=80,
            end_page=90,
            chunk_index=2,
        ),
    ]


def _make_use_case(
    *,
    book_repo: FakeBookRepository | None = None,
    chunk_repo: FakeChunkRepository | None = None,
    provider: FakeEmbeddingProvider | None = None,
    embedding_repo: FakeEmbeddingRepository | None = None,
) -> tuple[
    SearchBooksUseCase,
    FakeBookRepository,
    FakeChunkRepository,
    FakeEmbeddingProvider,
    FakeEmbeddingRepository,
]:
    br = book_repo or FakeBookRepository()
    cr = chunk_repo or FakeChunkRepository()
    ep = provider or FakeEmbeddingProvider()
    er = embedding_repo or FakeEmbeddingRepository()
    return (
        SearchBooksUseCase(
            embedding_provider=ep,
            book_repo=br,
            chunk_repo=cr,
            embedding_repo=er,
        ),
        br,
        cr,
        ep,
        er,
    )


class TestSearchSuccess:
    def test_returns_search_results_ordered_by_distance(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings()
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "test query")

        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].chunk_id == "c1"
        assert results[0].content == "Early content"
        assert results[0].distance == 0.1

    def test_embeds_query_text(self) -> None:
        use_case, book_repo, chunk_repo, provider, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings()
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1)])

        use_case.execute("book-1", "what is the meaning?")

        assert provider.last_texts == ["what is the meaning?"]

    def test_respects_top_k(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings()
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query", top_k=2)

        assert len(results) <= 2


class TestSearchBookNotFound:
    def test_raises_not_found(self) -> None:
        use_case, _, _, _, _ = _make_use_case()

        with pytest.raises(BookError) as exc_info:
            use_case.execute("nonexistent", "query")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestSearchNoEmbeddings:
    def test_raises_invalid_state(self) -> None:
        use_case, book_repo, _, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings()
        book.embedding_provider = None
        book.embedding_dimension = None
        book_repo.save(book)

        with pytest.raises(BookError) as exc_info:
            use_case.execute("book-1", "query")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE


class TestPageFiltering:
    def test_filters_chunks_beyond_current_page(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=50)
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        # All 3 returned from vector search, but c3 starts at page 80
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query")

        chunk_ids = [r.chunk_id for r in results]
        assert "c1" in chunk_ids
        assert "c2" in chunk_ids
        assert "c3" not in chunk_ids  # start_page=80 > current_page=50

    def test_no_filtering_when_current_page_is_zero(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=0)
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query")

        assert len(results) == 3

    def test_over_fetches_when_page_filtering_active(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=50)
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1)])

        use_case.execute("book-1", "query", top_k=5)

        assert embedding_repo.last_search_top_k == 15  # 5 * 3

    def test_does_not_over_fetch_when_no_page_filtering(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=0)
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1)])

        use_case.execute("book-1", "query", top_k=5)

        assert embedding_repo.last_search_top_k == 5


class TestPageOverride:
    def test_page_override_takes_precedence_over_current_page(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=0)  # no filtering by default
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query", page_override=50)

        chunk_ids = [r.chunk_id for r in results]
        assert "c1" in chunk_ids
        assert "c2" in chunk_ids
        assert "c3" not in chunk_ids  # start_page=80 > page_override=50

    def test_page_override_zero_disables_filtering_despite_current_page(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=50)  # filtering active
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query", page_override=0)

        assert len(results) == 3  # all chunks returned, filtering disabled

    def test_page_override_none_falls_back_to_current_page(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=50)
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1), ("c2", 0.5), ("c3", 0.9)])

        results = use_case.execute("book-1", "query", page_override=None)

        chunk_ids = [r.chunk_id for r in results]
        assert "c3" not in chunk_ids  # filtered by book.current_page=50

    def test_over_fetches_when_page_override_enables_filtering(self) -> None:
        use_case, book_repo, chunk_repo, _, embedding_repo = _make_use_case()
        book = _ready_book_with_embeddings(current_page=0)  # no filtering by default
        book_repo.save(book)
        chunk_repo.save_chunks("book-1", _chunks_with_pages())
        embedding_repo.set_search_results([("c1", 0.1)])

        use_case.execute("book-1", "query", top_k=5, page_override=50)

        assert embedding_repo.last_search_top_k == 15  # 5 * 3, over-fetch active
