from dataclasses import FrozenInstanceError

import pytest
from interactive_books.domain.chunk_data import ChunkData
from interactive_books.domain.errors import BookError, BookErrorCode


class TestChunkDataCreation:
    def test_create_valid_chunk_data(self) -> None:
        chunk = ChunkData(content="Some text", start_page=1, end_page=2, chunk_index=0)
        assert chunk.content == "Some text"
        assert chunk.start_page == 1
        assert chunk.end_page == 2
        assert chunk.chunk_index == 0

    def test_empty_content_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            ChunkData(content="", start_page=1, end_page=1, chunk_index=0)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_start_page_less_than_one_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            ChunkData(content="text", start_page=0, end_page=1, chunk_index=0)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_end_page_less_than_start_page_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            ChunkData(content="text", start_page=3, end_page=1, chunk_index=0)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_negative_chunk_index_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            ChunkData(content="text", start_page=1, end_page=1, chunk_index=-1)
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_single_page_chunk_is_valid(self) -> None:
        chunk = ChunkData(content="text", start_page=5, end_page=5, chunk_index=3)
        assert chunk.start_page == chunk.end_page


class TestChunkDataImmutability:
    def test_chunk_data_is_frozen(self) -> None:
        chunk = ChunkData(content="text", start_page=1, end_page=1, chunk_index=0)
        with pytest.raises(FrozenInstanceError):
            chunk.content = "modified"  # type: ignore[misc]
