from dataclasses import dataclass

from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass(frozen=True)
class EmbeddingVector:
    chunk_id: str
    vector: list[float]
    start_page: int
    end_page: int

    def __post_init__(self) -> None:
        if not self.vector:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                "EmbeddingVector vector cannot be empty",
            )
        if self.start_page < 1:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                f"EmbeddingVector start_page must be >= 1, got {self.start_page}",
            )
        if self.end_page < self.start_page:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                f"EmbeddingVector end_page ({self.end_page}) must be >= start_page ({self.start_page})",
            )
