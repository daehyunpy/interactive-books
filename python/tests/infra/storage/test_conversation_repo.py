from interactive_books.domain.book import Book
from interactive_books.domain.conversation import Conversation
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.conversation_repo import ConversationRepository
from interactive_books.infra.storage.database import Database


def _seed_book(db: Database, book_id: str = "b1") -> Book:
    book = Book(id=book_id, title="Test Book")
    BookRepository(db).save(book)
    return book


class TestConversationRepositorySave:
    def test_save_and_retrieve(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        conv = Conversation(id="c1", book_id="b1", title="About chapter 3")
        repo.save(conv)

        loaded = repo.get("c1")
        assert loaded is not None
        assert loaded.id == "c1"
        assert loaded.book_id == "b1"
        assert loaded.title == "About chapter 3"

    def test_save_updates_title_on_conflict(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        conv = Conversation(id="c1", book_id="b1", title="Old title")
        repo.save(conv)

        conv.rename("New title")
        repo.save(conv)

        loaded = repo.get("c1")
        assert loaded is not None
        assert loaded.title == "New title"


class TestConversationRepositoryGet:
    def test_get_returns_none_for_missing(self, db: Database) -> None:
        repo = ConversationRepository(db)
        assert repo.get("nonexistent") is None

    def test_get_by_book_returns_conversations_ordered(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        repo.save(Conversation(id="c1", book_id="b1", title="First"))
        repo.save(Conversation(id="c2", book_id="b1", title="Second"))
        repo.save(Conversation(id="c3", book_id="b1", title="Third"))

        results = repo.get_by_book("b1")
        assert len(results) == 3

    def test_get_by_book_empty(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        assert repo.get_by_book("b1") == []

    def test_get_by_book_filters_by_book(self, db: Database) -> None:
        _seed_book(db, "b1")
        _seed_book(db, "b2")
        repo = ConversationRepository(db)
        repo.save(Conversation(id="c1", book_id="b1", title="Book 1 conv"))
        repo.save(Conversation(id="c2", book_id="b2", title="Book 2 conv"))

        results = repo.get_by_book("b1")
        assert len(results) == 1
        assert results[0].book_id == "b1"


class TestConversationRepositoryDelete:
    def test_delete_removes_conversation(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        repo.save(Conversation(id="c1", book_id="b1", title="To delete"))
        repo.delete("c1")
        assert repo.get("c1") is None

    def test_delete_cascades_from_book(self, db: Database) -> None:
        _seed_book(db)
        repo = ConversationRepository(db)
        repo.save(Conversation(id="c1", book_id="b1", title="Will cascade"))

        BookRepository(db).delete("b1")
        assert repo.get("c1") is None
