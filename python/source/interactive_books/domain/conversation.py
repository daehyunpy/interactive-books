from dataclasses import dataclass, field
from datetime import datetime

from interactive_books.domain._time import utc_now
from interactive_books.domain.errors import BookError, BookErrorCode

EMPTY_TITLE_ERROR = "Conversation title cannot be empty"


@dataclass
class Conversation:
    id: str
    book_id: str
    title: str
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self._validate_title(self.title)

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title.strip():
            raise BookError(BookErrorCode.INVALID_STATE, EMPTY_TITLE_ERROR)
