from dataclasses import dataclass, field
from datetime import datetime

from interactive_books.domain._time import utc_now
from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass
class Conversation:
    id: str
    book_id: str
    title: str
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise BookError(
                BookErrorCode.INVALID_STATE, "Conversation title cannot be empty"
            )

    def rename(self, title: str) -> None:
        if not title.strip():
            raise BookError(
                BookErrorCode.INVALID_STATE, "Conversation title cannot be empty"
            )
        self.title = title
