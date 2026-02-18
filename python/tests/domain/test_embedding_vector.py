from dataclasses import FrozenInstanceError

import pytest
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.errors import BookError, BookErrorCode


class TestEmbeddingVectorCreation:
    def test_create_valid_embedding_vector(self) -> None:
        ev = EmbeddingVector(
            chunk_id="abc", vector=[0.1, 0.2, 0.3], start_page=1, end_page=3
        )
        assert ev.chunk_id == "abc"
        assert ev.vector == [0.1, 0.2, 0.3]
        assert ev.start_page == 1
        assert ev.end_page == 3

    def test_empty_vector_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            EmbeddingVector(chunk_id="abc", vector=[], start_page=1, end_page=1)
        assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_start_page_below_one_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            EmbeddingVector(chunk_id="abc", vector=[0.1], start_page=0, end_page=1)
        assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_end_page_below_start_page_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            EmbeddingVector(chunk_id="abc", vector=[0.1], start_page=5, end_page=3)
        assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_same_start_and_end_page_is_valid(self) -> None:
        ev = EmbeddingVector(chunk_id="abc", vector=[0.1], start_page=5, end_page=5)
        assert ev.start_page == 5
        assert ev.end_page == 5


class TestEmbeddingVectorImmutability:
    def test_embedding_vector_is_frozen(self) -> None:
        ev = EmbeddingVector(
            chunk_id="abc", vector=[0.1, 0.2], start_page=1, end_page=1
        )
        with pytest.raises(FrozenInstanceError):
            ev.chunk_id = "modified"  # type: ignore[misc]
