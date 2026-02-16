from datetime import datetime, timezone

import pytest

from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.errors import BookError, BookErrorCode


class TestBookStatus:
    def test_all_statuses_exist(self) -> None:
        expected = {"pending", "ingesting", "ready", "failed"}
        actual = {status.value for status in BookStatus}
        assert actual == expected

    def test_string_values_are_lowercase(self) -> None:
        assert BookStatus.PENDING.value == "pending"
        assert BookStatus.INGESTING.value == "ingesting"
        assert BookStatus.READY.value == "ready"
        assert BookStatus.FAILED.value == "failed"


class TestBookCreation:
    def test_create_book_with_valid_title(self) -> None:
        book = Book(id="abc", title="Clean Code")
        assert book.id == "abc"
        assert book.title == "Clean Code"
        assert book.status == BookStatus.PENDING
        assert book.current_page == 0
        assert book.embedding_provider is None
        assert book.embedding_dimension is None

    def test_create_book_with_empty_title_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Book(id="abc", title="")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_create_book_with_whitespace_title_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Book(id="abc", title="   ")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_create_book_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        book = Book(
            id="abc",
            title="DDD",
            status=BookStatus.READY,
            current_page=42,
            embedding_provider="openai",
            embedding_dimension=1536,
            created_at=now,
            updated_at=now,
        )
        assert book.status == BookStatus.READY
        assert book.current_page == 42
        assert book.embedding_provider == "openai"
        assert book.embedding_dimension == 1536
        assert book.created_at == now


class TestBookStatusTransitions:
    def test_start_ingestion_from_pending(self) -> None:
        book = Book(id="1", title="Test")
        book.start_ingestion()
        assert book.status == BookStatus.INGESTING

    def test_start_ingestion_from_ready_raises(self) -> None:
        book = Book(id="1", title="Test", status=BookStatus.READY)
        with pytest.raises(BookError) as exc_info:
            book.start_ingestion()
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_complete_ingestion_from_ingesting(self) -> None:
        book = Book(id="1", title="Test", status=BookStatus.INGESTING)
        book.complete_ingestion()
        assert book.status == BookStatus.READY

    def test_complete_ingestion_from_pending_raises(self) -> None:
        book = Book(id="1", title="Test")
        with pytest.raises(BookError) as exc_info:
            book.complete_ingestion()
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_fail_ingestion_from_ingesting(self) -> None:
        book = Book(id="1", title="Test", status=BookStatus.INGESTING)
        book.fail_ingestion()
        assert book.status == BookStatus.FAILED

    def test_fail_ingestion_from_pending_raises(self) -> None:
        book = Book(id="1", title="Test")
        with pytest.raises(BookError) as exc_info:
            book.fail_ingestion()
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_reset_to_pending_from_any_status(self) -> None:
        for status in BookStatus:
            book = Book(id="1", title="Test", status=status)
            book.reset_to_pending()
            assert book.status == BookStatus.PENDING


class TestBookCurrentPage:
    def test_set_current_page_valid(self) -> None:
        book = Book(id="1", title="Test")
        book.set_current_page(10)
        assert book.current_page == 10

    def test_set_current_page_zero(self) -> None:
        book = Book(id="1", title="Test", current_page=5)
        book.set_current_page(0)
        assert book.current_page == 0

    def test_set_current_page_negative_raises(self) -> None:
        book = Book(id="1", title="Test")
        with pytest.raises(BookError) as exc_info:
            book.set_current_page(-1)
        assert exc_info.value.code == BookErrorCode.INVALID_STATE


class TestBookEmbeddingProvider:
    def test_switch_embedding_provider(self) -> None:
        book = Book(id="1", title="Test", status=BookStatus.READY)
        book.switch_embedding_provider("openai", 1536)
        assert book.embedding_provider == "openai"
        assert book.embedding_dimension == 1536
        assert book.status == BookStatus.PENDING

    def test_switch_provider_resets_status_to_pending(self) -> None:
        book = Book(id="1", title="Test", status=BookStatus.FAILED)
        book.switch_embedding_provider("ollama", 768)
        assert book.status == BookStatus.PENDING
