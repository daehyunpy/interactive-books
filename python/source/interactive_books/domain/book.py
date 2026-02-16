from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from interactive_books.domain.errors import BookError, BookErrorCode


class BookStatus(Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    READY = "ready"
    FAILED = "failed"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Book:
    id: str
    title: str
    status: BookStatus = BookStatus.PENDING
    current_page: int = 0
    embedding_provider: str | None = None
    embedding_dimension: int | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise BookError(BookErrorCode.INVALID_STATE, "Book title cannot be empty")

    def start_ingestion(self) -> None:
        if self.status != BookStatus.PENDING:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Cannot start ingestion from '{self.status.value}' status",
            )
        self.status = BookStatus.INGESTING

    def complete_ingestion(self) -> None:
        if self.status != BookStatus.INGESTING:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Cannot complete ingestion from '{self.status.value}' status",
            )
        self.status = BookStatus.READY

    def fail_ingestion(self) -> None:
        if self.status != BookStatus.INGESTING:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Cannot fail ingestion from '{self.status.value}' status",
            )
        self.status = BookStatus.FAILED

    def reset_to_pending(self) -> None:
        self.status = BookStatus.PENDING

    def set_current_page(self, page: int) -> None:
        if page < 0:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Current page cannot be negative: {page}",
            )
        self.current_page = page

    def switch_embedding_provider(self, provider: str, dimension: int) -> None:
        self.embedding_provider = provider
        self.embedding_dimension = dimension
        self.reset_to_pending()
