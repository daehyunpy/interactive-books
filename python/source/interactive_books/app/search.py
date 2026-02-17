from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    BookRepository,
    ChunkRepository,
    EmbeddingProvider,
    EmbeddingRepository,
)
from interactive_books.domain.search_result import SearchResult

OVER_FETCH_MULTIPLIER = 3


class SearchBooksUseCase:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        self._provider = embedding_provider
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo

    def execute(
        self,
        book_id: str,
        query: str,
        top_k: int = 5,
        page_override: int | None = None,
    ) -> list[SearchResult]:
        book = self._book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book '{book_id}' not found")

        if not book.embedding_provider or not book.embedding_dimension:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Book '{book_id}' has no embeddings",
            )

        provider_name = book.embedding_provider
        dimension = book.embedding_dimension
        effective_page = page_override if page_override is not None else book.current_page
        page_filtering = effective_page > 0
        fetch_k = top_k * OVER_FETCH_MULTIPLIER if page_filtering else top_k

        query_vector = self._provider.embed([query])[0]

        hits = self._embedding_repo.search(
            provider_name, dimension, book_id, query_vector, fetch_k
        )

        if not hits:
            return []

        chunks = self._chunk_repo.get_by_book(book_id)
        chunk_map = {c.id: c for c in chunks}

        results: list[SearchResult] = []
        for chunk_id, distance in hits:
            chunk = chunk_map.get(chunk_id)
            if chunk is None:
                continue
            if page_filtering and chunk.start_page > effective_page:
                continue
            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    content=chunk.content,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    distance=distance,
                )
            )

        return results[:top_k]
