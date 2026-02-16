from dataclasses import dataclass, field
from datetime import datetime, timezone

from interactive_books.domain.errors import BookError, BookErrorCode


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Chunk:
    id: str
    book_id: str
    content: str
    start_page: int
    end_page: int
    chunk_index: int
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.start_page < 1:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Chunk start_page must be >= 1, got {self.start_page}",
            )
        if self.end_page < self.start_page:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Chunk end_page ({self.end_page}) must be >= start_page ({self.start_page})",
            )
