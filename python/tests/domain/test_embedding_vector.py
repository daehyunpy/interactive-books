from dataclasses import FrozenInstanceError

import pytest
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.errors import BookError, BookErrorCode


class TestEmbeddingVectorCreation:
    def test_create_valid_embedding_vector(self) -> None:
        ev = EmbeddingVector(chunk_id="abc", vector=[0.1, 0.2, 0.3])
        assert ev.chunk_id == "abc"
        assert ev.vector == [0.1, 0.2, 0.3]

    def test_empty_vector_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            EmbeddingVector(chunk_id="abc", vector=[])
        assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED


class TestEmbeddingVectorImmutability:
    def test_embedding_vector_is_frozen(self) -> None:
        ev = EmbeddingVector(chunk_id="abc", vector=[0.1, 0.2])
        with pytest.raises(FrozenInstanceError):
            ev.chunk_id = "modified"  # type: ignore[misc]
