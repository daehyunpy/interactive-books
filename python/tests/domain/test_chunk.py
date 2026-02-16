from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode


class TestChunkCreation:
    def test_create_valid_chunk(self) -> None:
        now = datetime.now(timezone.utc)
        chunk = Chunk(
            id="c1",
            book_id="b1",
            content="Some text",
            start_page=1,
            end_page=3,
            chunk_index=0,
            created_at=now,
        )
        assert chunk.id == "c1"
        assert chunk.book_id == "b1"
        assert chunk.content == "Some text"
        assert chunk.start_page == 1
        assert chunk.end_page == 3
        assert chunk.chunk_index == 0
        assert chunk.created_at == now

    def test_start_page_less_than_one_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Chunk(id="c1", book_id="b1", content="x", start_page=0, end_page=1, chunk_index=0)
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_end_page_less_than_start_page_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Chunk(id="c1", book_id="b1", content="x", start_page=5, end_page=3, chunk_index=0)
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_single_page_chunk_is_valid(self) -> None:
        chunk = Chunk(id="c1", book_id="b1", content="x", start_page=1, end_page=1, chunk_index=0)
        assert chunk.start_page == chunk.end_page


class TestChunkImmutability:
    def test_chunk_is_frozen(self) -> None:
        chunk = Chunk(id="c1", book_id="b1", content="x", start_page=1, end_page=1, chunk_index=0)
        with pytest.raises(FrozenInstanceError):
            chunk.content = "modified"  # type: ignore[misc]
