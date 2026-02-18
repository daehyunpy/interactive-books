from dataclasses import dataclass, field
from datetime import datetime

from interactive_books.domain._time import utc_now
from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass(frozen=True)
class KeyStatement:
    statement: str
    page: int

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise BookError(
                BookErrorCode.INVALID_STATE,
                "KeyStatement statement cannot be empty",
            )
        if self.page < 1:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"KeyStatement page must be >= 1, got {self.page}",
            )


@dataclass(frozen=True)
class SectionSummary:
    id: str
    book_id: str
    title: str
    start_page: int
    end_page: int
    summary: str
    key_statements: list[KeyStatement]
    section_index: int
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise BookError(
                BookErrorCode.INVALID_STATE,
                "SectionSummary title cannot be empty",
            )
        if not self.summary.strip():
            raise BookError(
                BookErrorCode.INVALID_STATE,
                "SectionSummary summary cannot be empty",
            )
        if self.start_page < 1:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"SectionSummary start_page must be >= 1, got {self.start_page}",
            )
        if self.end_page < self.start_page:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"SectionSummary end_page ({self.end_page}) must be >= start_page ({self.start_page})",
            )
