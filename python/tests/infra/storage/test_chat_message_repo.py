from interactive_books.domain.book import Book
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.conversation import Conversation
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chat_message_repo import ChatMessageRepository
from interactive_books.infra.storage.conversation_repo import ConversationRepository
from interactive_books.infra.storage.database import Database


def _seed_conversation(db: Database, conv_id: str = "c1") -> Conversation:
    BookRepository(db).save(Book(id="b1", title="Test Book"))
    conv = Conversation(id=conv_id, book_id="b1", title="Test Conversation")
    ConversationRepository(db).save(conv)
    return conv


class TestChatMessageRepositorySave:
    def test_save_and_retrieve(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        msg = ChatMessage(
            id="m1", conversation_id="c1", role=MessageRole.USER, content="Hello"
        )
        repo.save(msg)

        messages = repo.get_by_conversation("c1")
        assert len(messages) == 1
        assert messages[0].id == "m1"
        assert messages[0].conversation_id == "c1"
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"

    def test_save_tool_result_message(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        msg = ChatMessage(
            id="m1",
            conversation_id="c1",
            role=MessageRole.TOOL_RESULT,
            content="[Pages 1-5]: Some content.",
        )
        repo.save(msg)

        messages = repo.get_by_conversation("c1")
        assert messages[0].role == MessageRole.TOOL_RESULT


class TestChatMessageRepositoryGetByConversation:
    def test_returns_chronological_order(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        repo.save(
            ChatMessage(
                id="m1", conversation_id="c1", role=MessageRole.USER, content="Q1"
            )
        )
        repo.save(
            ChatMessage(
                id="m2",
                conversation_id="c1",
                role=MessageRole.ASSISTANT,
                content="A1",
            )
        )
        repo.save(
            ChatMessage(
                id="m3", conversation_id="c1", role=MessageRole.USER, content="Q2"
            )
        )

        messages = repo.get_by_conversation("c1")
        assert len(messages) == 3
        assert [m.id for m in messages] == ["m1", "m2", "m3"]

    def test_empty_conversation_returns_empty(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        assert repo.get_by_conversation("c1") == []

    def test_messages_filtered_by_conversation(self, db: Database) -> None:
        _seed_conversation(db, "c1")
        ConversationRepository(db).save(
            Conversation(id="c2", book_id="b1", title="Other conv")
        )
        repo = ChatMessageRepository(db)
        repo.save(
            ChatMessage(
                id="m1", conversation_id="c1", role=MessageRole.USER, content="In c1"
            )
        )
        repo.save(
            ChatMessage(
                id="m2", conversation_id="c2", role=MessageRole.USER, content="In c2"
            )
        )

        assert len(repo.get_by_conversation("c1")) == 1
        assert len(repo.get_by_conversation("c2")) == 1


class TestChatMessageRepositoryDelete:
    def test_delete_by_conversation(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        repo.save(
            ChatMessage(
                id="m1", conversation_id="c1", role=MessageRole.USER, content="Q"
            )
        )
        repo.save(
            ChatMessage(
                id="m2",
                conversation_id="c1",
                role=MessageRole.ASSISTANT,
                content="A",
            )
        )

        repo.delete_by_conversation("c1")
        assert repo.get_by_conversation("c1") == []

    def test_delete_cascades_from_conversation(self, db: Database) -> None:
        _seed_conversation(db)
        repo = ChatMessageRepository(db)
        repo.save(
            ChatMessage(
                id="m1", conversation_id="c1", role=MessageRole.USER, content="Q"
            )
        )

        ConversationRepository(db).delete("c1")
        assert repo.get_by_conversation("c1") == []

    def test_delete_other_conversation_unaffected(self, db: Database) -> None:
        _seed_conversation(db, "c1")
        ConversationRepository(db).save(
            Conversation(id="c2", book_id="b1", title="Other")
        )
        repo = ChatMessageRepository(db)
        repo.save(
            ChatMessage(
                id="m1", conversation_id="c1", role=MessageRole.USER, content="In c1"
            )
        )
        repo.save(
            ChatMessage(
                id="m2", conversation_id="c2", role=MessageRole.USER, content="In c2"
            )
        )

        repo.delete_by_conversation("c1")
        assert len(repo.get_by_conversation("c2")) == 1
