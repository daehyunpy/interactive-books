from datetime import datetime, timezone

from interactive_books.domain.book import Book, BookStatus
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.database import Database


class TestBookRepository:
    def test_save_and_get(self, db: Database) -> None:
        repo = BookRepository(db)
        book = Book(id="b1", title="Clean Code")
        repo.save(book)

        loaded = repo.get("b1")
        assert loaded is not None
        assert loaded.id == "b1"
        assert loaded.title == "Clean Code"
        assert loaded.status == BookStatus.PENDING
        assert loaded.current_page == 0
        assert loaded.embedding_provider is None
        assert loaded.embedding_dimension is None

    def test_get_returns_none_for_missing(self, db: Database) -> None:
        repo = BookRepository(db)
        assert repo.get("nonexistent") is None

    def test_get_all_empty(self, db: Database) -> None:
        repo = BookRepository(db)
        assert repo.get_all() == []

    def test_get_all_returns_all_books(self, db: Database) -> None:
        repo = BookRepository(db)
        repo.save(Book(id="b1", title="Book One"))
        repo.save(Book(id="b2", title="Book Two"))

        books = repo.get_all()
        assert len(books) == 2
        ids = {b.id for b in books}
        assert ids == {"b1", "b2"}

    def test_delete_removes_book(self, db: Database) -> None:
        repo = BookRepository(db)
        repo.save(Book(id="b1", title="Delete Me"))
        repo.delete("b1")
        assert repo.get("b1") is None

    def test_delete_nonexistent_is_noop(self, db: Database) -> None:
        repo = BookRepository(db)
        repo.delete("nonexistent")  # should not raise

    def test_save_updates_existing_book(self, db: Database) -> None:
        repo = BookRepository(db)
        book = Book(id="b1", title="Original")
        repo.save(book)

        book.start_ingestion()
        book.complete_ingestion()
        book.set_current_page(42)
        repo.save(book)

        loaded = repo.get("b1")
        assert loaded is not None
        assert loaded.status == BookStatus.READY
        assert loaded.current_page == 42

    def test_save_preserves_embedding_fields(self, db: Database) -> None:
        repo = BookRepository(db)
        book = Book(
            id="b1",
            title="Embeddings",
            embedding_provider="openai",
            embedding_dimension=1536,
        )
        repo.save(book)

        loaded = repo.get("b1")
        assert loaded is not None
        assert loaded.embedding_provider == "openai"
        assert loaded.embedding_dimension == 1536

    def test_save_preserves_timestamps(self, db: Database) -> None:
        repo = BookRepository(db)
        now = datetime.now(timezone.utc)
        book = Book(id="b1", title="Timestamps", created_at=now, updated_at=now)
        repo.save(book)

        loaded = repo.get("b1")
        assert loaded is not None
        assert loaded.created_at == now
        assert loaded.updated_at == now
