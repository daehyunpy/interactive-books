from interactive_books.domain.book import Book
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.conversation import Conversation
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chat_message_repo import ChatMessageRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.conversation_repo import ConversationRepository
from interactive_books.infra.storage.database import Database


class TestCascadeDelete:
    def test_deleting_book_cascades_to_chunks(self, db: Database) -> None:
        book_repo = BookRepository(db)
        chunk_repo = ChunkRepository(db)

        book_repo.save(Book(id="b1", title="Cascade Test"))
        chunk_repo.save_chunks(
            "b1",
            [
                Chunk(
                    id="c1",
                    book_id="b1",
                    content="A",
                    start_page=1,
                    end_page=1,
                    chunk_index=0,
                ),
                Chunk(
                    id="c2",
                    book_id="b1",
                    content="B",
                    start_page=2,
                    end_page=2,
                    chunk_index=1,
                ),
            ],
        )

        book_repo.delete("b1")
        assert chunk_repo.get_by_book("b1") == []

    def test_deleting_book_cascades_to_conversations_and_messages(
        self, db: Database
    ) -> None:
        book_repo = BookRepository(db)
        conv_repo = ConversationRepository(db)
        msg_repo = ChatMessageRepository(db)

        book_repo.save(Book(id="b1", title="Cascade Test"))
        conv_repo.save(Conversation(id="conv-1", book_id="b1", title="Chat"))
        msg_repo.save(
            ChatMessage(
                id="m1",
                conversation_id="conv-1",
                role=MessageRole.USER,
                content="Hello",
            )
        )

        book_repo.delete("b1")

        assert conv_repo.get("conv-1") is None
        assert msg_repo.get_by_conversation("conv-1") == []

    def test_deleting_book_does_not_affect_other_books(self, db: Database) -> None:
        book_repo = BookRepository(db)
        chunk_repo = ChunkRepository(db)

        book_repo.save(Book(id="b1", title="Delete Me"))
        book_repo.save(Book(id="b2", title="Keep Me"))
        chunk_repo.save_chunks(
            "b1",
            [
                Chunk(
                    id="c1",
                    book_id="b1",
                    content="A",
                    start_page=1,
                    end_page=1,
                    chunk_index=0,
                ),
            ],
        )
        chunk_repo.save_chunks(
            "b2",
            [
                Chunk(
                    id="c2",
                    book_id="b2",
                    content="B",
                    start_page=1,
                    end_page=1,
                    chunk_index=0,
                ),
            ],
        )

        book_repo.delete("b1")

        assert book_repo.get("b2") is not None
        assert len(chunk_repo.get_by_book("b2")) == 1
