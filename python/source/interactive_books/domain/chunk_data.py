from dataclasses import dataclass

from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass(frozen=True)
class ChunkData:
    content: str
    start_page: int
    end_page: int
    chunk_index: int

    def __post_init__(self) -> None:
        if not self.content:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                "ChunkData content cannot be empty",
            )
        if self.start_page < 1:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"ChunkData start_page must be >= 1, got {self.start_page}",
            )
        if self.end_page < self.start_page:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"ChunkData end_page ({self.end_page}) must be >= start_page ({self.start_page})",
            )
        if self.chunk_index < 0:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"ChunkData chunk_index must be >= 0, got {self.chunk_index}",
            )
