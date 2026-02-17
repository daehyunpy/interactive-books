import pytest
from interactive_books.domain.search_result import SearchResult


class TestSearchResult:
    def test_creation(self) -> None:
        result = SearchResult(
            chunk_id="c1",
            content="some text",
            start_page=1,
            end_page=2,
            distance=0.5,
        )

        assert result.chunk_id == "c1"
        assert result.content == "some text"
        assert result.start_page == 1
        assert result.end_page == 2
        assert result.distance == 0.5

    def test_is_frozen(self) -> None:
        result = SearchResult(
            chunk_id="c1",
            content="text",
            start_page=1,
            end_page=1,
            distance=0.1,
        )

        with pytest.raises(AttributeError):
            result.distance = 0.9  # type: ignore[misc]
