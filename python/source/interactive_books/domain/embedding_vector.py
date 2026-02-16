from dataclasses import dataclass

from interactive_books.domain.errors import BookError, BookErrorCode


@dataclass(frozen=True)
class EmbeddingVector:
    chunk_id: str
    vector: list[float]

    def __post_init__(self) -> None:
        if not self.vector:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                "EmbeddingVector vector cannot be empty",
            )
