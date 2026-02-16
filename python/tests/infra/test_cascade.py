from interactive_books.domain.book import Book
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.chunk import Chunk
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.database import Database


class TestCascadeDelete:
    def test_deleting_book_cascades_to_chunks(self, db: Database) -> None:
        book_repo = BookRepository(db)
        chunk_repo = ChunkRepository(db)

        book_repo.save(Book(id="b1", title="Cascade Test"))
        chunk_repo.save_chunks("b1", [
            Chunk(id="c1", book_id="b1", content="A", start_page=1, end_page=1, chunk_index=0),
            Chunk(id="c2", book_id="b1", content="B", start_page=2, end_page=2, chunk_index=1),
        ])

        book_repo.delete("b1")
        assert chunk_repo.get_by_book("b1") == []

    def test_deleting_book_cascades_to_chat_messages(self, db: Database) -> None:
        book_repo = BookRepository(db)

        book_repo.save(Book(id="b1", title="Cascade Test"))

        # Insert chat messages directly (no ChatMessageRepository yet)
        msg = ChatMessage(id="m1", book_id="b1", role=MessageRole.USER, content="Hello")
        db.connection.execute(
            "INSERT INTO chat_messages (id, book_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg.id, msg.book_id, msg.role.value, msg.content, msg.created_at.isoformat()),
        )
        db.connection.commit()

        book_repo.delete("b1")

        cursor = db.connection.execute("SELECT COUNT(*) FROM chat_messages WHERE book_id = ?", ("b1",))
        assert cursor.fetchone()[0] == 0

    def test_deleting_book_does_not_affect_other_books(self, db: Database) -> None:
        book_repo = BookRepository(db)
        chunk_repo = ChunkRepository(db)

        book_repo.save(Book(id="b1", title="Delete Me"))
        book_repo.save(Book(id="b2", title="Keep Me"))
        chunk_repo.save_chunks("b1", [
            Chunk(id="c1", book_id="b1", content="A", start_page=1, end_page=1, chunk_index=0),
        ])
        chunk_repo.save_chunks("b2", [
            Chunk(id="c2", book_id="b2", content="B", start_page=1, end_page=1, chunk_index=0),
        ])

        book_repo.delete("b1")

        assert book_repo.get("b2") is not None
        assert len(chunk_repo.get_by_book("b2")) == 1
