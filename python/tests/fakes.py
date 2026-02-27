from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.embedding_vector import EmbeddingVector


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

    def get_by_page_range(
        self, book_id: str, start_page: int, end_page: int
    ) -> list[Chunk]:
        return [
            c
            for c in self.get_by_book(book_id)
            if c.start_page <= end_page and c.end_page >= start_page
        ]

    def count_by_book(self, book_id: str) -> int:
        return len(self.chunks.get(book_id, []))

    def delete_by_book(self, book_id: str) -> None:
        self.chunks.pop(book_id, None)


class FakeEmbeddingProvider:
    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension
        self.call_count = 0
        self.last_texts: list[str] = []

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        self.last_texts = texts
        return [[0.1] * self._dimension for _ in texts]


class FakeEmbeddingRepository:
    """Fake embedding repository that supports both search results and storage tracking."""

    def __init__(self) -> None:
        self._search_results: list[tuple[str, float, int, int]] = []
        self.last_search_top_k: int | None = None
        self.tables: set[str] = set()
        self.embeddings: dict[str, list[tuple[str, EmbeddingVector]]] = {}

    def set_search_results(self, results: list[tuple[str, float, int, int]]) -> None:
        self._search_results = results

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
    ) -> list[tuple[str, float, int, int]]:
        self.last_search_top_k = top_k
        return self._search_results[:top_k]

    def count_for_book(self, book_id: str, provider_name: str, dimension: int) -> int:
        key = f"{provider_name}_{dimension}"
        return sum(1 for bid, _ in self.embeddings.get(key, []) if bid == book_id)
