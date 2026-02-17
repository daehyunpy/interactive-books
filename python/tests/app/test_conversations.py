import pytest
from interactive_books.app.conversations import ManageConversationsUseCase
from interactive_books.domain.book import Book
from interactive_books.domain.conversation import Conversation
from interactive_books.domain.errors import BookError, BookErrorCode


class FakeBookRepository:
    def __init__(self, books: list[Book] | None = None) -> None:
        self._books = {b.id: b for b in (books or [])}

    def save(self, book: Book) -> None:
        self._books[book.id] = book

    def get(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self._books.values())

    def delete(self, book_id: str) -> None:
        self._books.pop(book_id, None)


class FakeConversationRepository:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._conversations[conversation.id] = conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def get_by_book(self, book_id: str) -> list[Conversation]:
        return [c for c in self._conversations.values() if c.book_id == book_id]

    def delete(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)


def _make_use_case(
    *, books: list[Book] | None = None
) -> tuple[ManageConversationsUseCase, FakeConversationRepository]:
    book_repo = FakeBookRepository(books)
    conv_repo = FakeConversationRepository()
    use_case = ManageConversationsUseCase(
        conversation_repo=conv_repo, book_repo=book_repo
    )
    return use_case, conv_repo


class TestCreateConversation:
    def test_creates_with_explicit_title(self) -> None:
        use_case, conv_repo = _make_use_case(books=[Book(id="b1", title="My Book")])
        conv = use_case.create("b1", title="About chapter 3")
        assert conv.book_id == "b1"
        assert conv.title == "About chapter 3"
        assert conv_repo.get(conv.id) is not None

    def test_creates_with_default_title(self) -> None:
        use_case, _ = _make_use_case(books=[Book(id="b1", title="My Book")])
        conv = use_case.create("b1")
        assert conv.title == "New conversation"

    def test_create_raises_for_missing_book(self) -> None:
        use_case, _ = _make_use_case()
        with pytest.raises(BookError) as exc_info:
            use_case.create("nonexistent")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestListConversations:
    def test_lists_conversations_for_book(self) -> None:
        use_case, _ = _make_use_case(books=[Book(id="b1", title="Book")])
        use_case.create("b1", "Conv 1")
        use_case.create("b1", "Conv 2")
        result = use_case.list_by_book("b1")
        assert len(result) == 2

    def test_empty_list_for_book_with_no_conversations(self) -> None:
        use_case, _ = _make_use_case(books=[Book(id="b1", title="Book")])
        assert use_case.list_by_book("b1") == []


class TestRenameConversation:
    def test_renames_conversation(self) -> None:
        use_case, _ = _make_use_case(books=[Book(id="b1", title="Book")])
        conv = use_case.create("b1", "Old title")
        renamed = use_case.rename(conv.id, "New title")
        assert renamed.title == "New title"

    def test_rename_raises_for_missing(self) -> None:
        use_case, _ = _make_use_case()
        with pytest.raises(BookError) as exc_info:
            use_case.rename("nonexistent", "title")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestDeleteConversation:
    def test_deletes_conversation(self) -> None:
        use_case, conv_repo = _make_use_case(books=[Book(id="b1", title="Book")])
        conv = use_case.create("b1", "To delete")
        use_case.delete(conv.id)
        assert conv_repo.get(conv.id) is None

    def test_delete_raises_for_missing(self) -> None:
        use_case, _ = _make_use_case()
        with pytest.raises(BookError) as exc_info:
            use_case.delete("nonexistent")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestAutoTitle:
    def test_short_message_used_as_is(self) -> None:
        assert (
            ManageConversationsUseCase.auto_title("What is chapter 3?")
            == "What is chapter 3?"
        )

    def test_long_message_truncated(self) -> None:
        long_msg = "A" * 100
        title = ManageConversationsUseCase.auto_title(long_msg)
        assert len(title) <= 63  # 60 + "..."
        assert title.endswith("...")

    def test_empty_message_uses_default(self) -> None:
        assert ManageConversationsUseCase.auto_title("") == "New conversation"
        assert ManageConversationsUseCase.auto_title("   ") == "New conversation"
