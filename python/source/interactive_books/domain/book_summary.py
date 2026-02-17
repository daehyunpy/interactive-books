from dataclasses import dataclass

from interactive_books.domain.book import BookStatus


@dataclass(frozen=True)
class BookSummary:
    id: str
    title: str
    status: BookStatus
    chunk_count: int
    embedding_provider: str | None
    current_page: int
