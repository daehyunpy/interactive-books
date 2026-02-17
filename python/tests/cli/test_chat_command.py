from interactive_books.domain.conversation import Conversation
from interactive_books.main import _select_or_create_conversation, app


class FakeManageConversations:
    """Minimal fake for ManageConversationsUseCase."""

    def __init__(self, conversations: list[Conversation] | None = None) -> None:
        self._conversations = conversations or []
        self.created_book_id: str | None = None

    def list_by_book(self, book_id: str) -> list[Conversation]:
        return [c for c in self._conversations if c.book_id == book_id]

    def create(self, book_id: str, title: str | None = None) -> Conversation:
        self.created_book_id = book_id
        return Conversation(id="new-conv", book_id=book_id, title="New conversation")


def _command_names() -> list[str]:
    """Extract effective command names from Typer app (name or callback.__name__)."""
    names = []
    for cmd in app.registered_commands:
        if cmd.name:
            names.append(cmd.name)
        elif cmd.callback:
            names.append(cmd.callback.__name__)
    return names


class TestCommandRegistration:
    def test_chat_command_is_registered(self) -> None:
        assert "chat" in _command_names()

    def test_ask_command_is_not_registered(self) -> None:
        assert "ask" not in _command_names()


class TestSelectOrCreateConversation:
    def test_creates_new_when_no_existing(self) -> None:
        manage = FakeManageConversations()

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.book_id == "book-1"
        assert manage.created_book_id == "book-1"

    def test_creates_new_when_user_selects_n(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        # Simulate user typing "N" at the prompt
        inputs = iter(["N"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "new-conv"
        assert manage.created_book_id == "book-1"

    def test_selects_existing_by_number(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
            Conversation(id="conv-2", book_id="book-1", title="Second chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        inputs = iter(["2"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "conv-2"

    def test_invalid_choice_creates_new(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        inputs = iter(["99"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "new-conv"
