from dataclasses import dataclass

from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass(frozen=True)
class PageContent:
    page_number: int
    text: str

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"Page number must be >= 1, got {self.page_number}",
            )
