import pytest
from interactive_books.domain.book import BookStatus
from interactive_books.domain.book_summary import BookSummary


class TestBookSummary:
    def test_creation(self) -> None:
        summary = BookSummary(
            id="b1",
            title="Test Book",
            status=BookStatus.READY,
            chunk_count=42,
            embedding_provider="openai",
            current_page=10,
        )

        assert summary.id == "b1"
        assert summary.title == "Test Book"
        assert summary.status == BookStatus.READY
        assert summary.chunk_count == 42
        assert summary.embedding_provider == "openai"
        assert summary.current_page == 10

    def test_embedding_provider_none(self) -> None:
        summary = BookSummary(
            id="b1",
            title="No Embeddings",
            status=BookStatus.PENDING,
            chunk_count=0,
            embedding_provider=None,
            current_page=0,
        )

        assert summary.embedding_provider is None

    def test_is_frozen(self) -> None:
        summary = BookSummary(
            id="b1",
            title="Frozen",
            status=BookStatus.READY,
            chunk_count=5,
            embedding_provider=None,
            current_page=0,
        )

        with pytest.raises(AttributeError):
            summary.chunk_count = 99  # type: ignore[misc]
