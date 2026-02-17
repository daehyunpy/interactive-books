from interactive_books.domain.book import Book
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import BookRepository, EmbeddingRepository


class DeleteBookUseCase:
    def __init__(
        self, *, book_repo: BookRepository, embedding_repo: EmbeddingRepository
    ) -> None:
        self._book_repo = book_repo
        self._embedding_repo = embedding_repo

    def execute(self, book_id: str) -> Book:
        book = self._book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book not found: {book_id}")

        if book.embedding_provider is not None and book.embedding_dimension is not None:
            self._embedding_repo.delete_by_book(
                book.embedding_provider, book.embedding_dimension, book_id
            )

        self._book_repo.delete(book_id)
        return book
