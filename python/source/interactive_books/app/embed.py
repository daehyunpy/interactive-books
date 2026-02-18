from collections.abc import Callable

from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    BookRepository,
    ChunkRepository,
    EmbeddingProvider,
    EmbeddingRepository,
)

DEFAULT_BATCH_SIZE = 100


class EmbedBookUseCase:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
        batch_size: int = DEFAULT_BATCH_SIZE,
        on_progress: Callable[[int, int, int], None] | None = None,
    ) -> None:
        self._provider = embedding_provider
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo
        self._batch_size = batch_size
        self._on_progress = on_progress

    def execute(self, book_id: str) -> Book:
        book = self._book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book '{book_id}' not found")

        chunks = self._chunk_repo.get_by_book(book_id)
        if not chunks:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Book '{book_id}' has no chunks to embed",
            )

        provider_name = self._provider.provider_name
        dimension = self._provider.dimension

        self._embedding_repo.ensure_table(provider_name, dimension)
        self._embedding_repo.delete_by_book(provider_name, dimension, book_id)

        try:
            vectors = self._embed_in_batches(chunks)
            self._embedding_repo.save_embeddings(
                provider_name, dimension, book_id, vectors
            )
        except Exception:
            self._embedding_repo.delete_by_book(provider_name, dimension, book_id)
            raise

        book.embedding_provider = provider_name
        book.embedding_dimension = dimension
        self._book_repo.save(book)

        return book

    def _embed_in_batches(self, chunks: list[Chunk]) -> list[EmbeddingVector]:
        all_vectors: list[EmbeddingVector] = []
        total_batches = (len(chunks) + self._batch_size - 1) // self._batch_size
        for i in range(0, len(chunks), self._batch_size):
            batch = chunks[i : i + self._batch_size]
            batch_num = i // self._batch_size + 1
            if self._on_progress:
                self._on_progress(batch_num, total_batches, len(batch))
            texts = [c.content for c in batch]
            vectors = self._provider.embed(texts)
            all_vectors.extend(
                EmbeddingVector(
                    chunk_id=chunk.id,
                    vector=vec,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                )
                for chunk, vec in zip(batch, vectors)
            )
        return all_vectors
