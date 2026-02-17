from interactive_books.domain.book_summary import BookSummary
from interactive_books.domain.protocols import BookRepository, ChunkRepository


class ListBooksUseCase:
    def __init__(
        self, *, book_repo: BookRepository, chunk_repo: ChunkRepository
    ) -> None:
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo

    def execute(self) -> list[BookSummary]:
        books = self._book_repo.get_all()
        return [
            BookSummary(
                id=book.id,
                title=book.title,
                status=book.status,
                chunk_count=self._chunk_repo.count_by_book(book.id),
                embedding_provider=book.embedding_provider,
                current_page=book.current_page,
            )
            for book in books
        ]
