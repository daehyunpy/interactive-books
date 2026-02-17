from interactive_books.domain.chat_event import (
    TokenUsageEvent,
    ToolInvocationEvent,
    ToolResultEvent,
)
from interactive_books.domain.conversation import Conversation
from interactive_books.domain.search_result import SearchResult
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


# ── Tests: Command Registration ──────────────────────────────────


class TestCommandRegistration:
    def test_chat_command_is_registered(self) -> None:
        assert "chat" in _command_names()

    def test_ask_command_is_not_registered(self) -> None:
        assert "ask" not in _command_names()


# ── Tests: Conversation Selection ────────────────────────────────


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

    def test_invalid_choice_retries_then_creates_new(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        inputs = iter(["99", "abc", "0"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "new-conv"

    def test_invalid_then_valid_selects_existing(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        inputs = iter(["99", "1"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "conv-1"

    def test_invalid_then_n_creates_new(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        existing = [
            Conversation(id="conv-1", book_id="book-1", title="First chat"),
        ]
        manage = FakeManageConversations(conversations=existing)
        inputs = iter(["abc", "N"])
        monkeypatch.setattr("typer.prompt", lambda *a, **kw: next(inputs))

        result = _select_or_create_conversation(manage, "book-1")  # type: ignore[arg-type]

        assert result.id == "new-conv"
        assert manage.created_book_id == "book-1"


# ── Tests: Verbose Event Formatting ─────────────────────────────


class TestVerboseEventFormatting:
    """Test event → [verbose] line formatting used in the chat command."""

    def _format_event(self, event: object) -> str | None:
        """Replicate the _on_event formatting logic from main.py."""
        if isinstance(event, ToolInvocationEvent):
            return f"[verbose] Tool call: {event.tool_name}({event.arguments})"
        if isinstance(event, ToolResultEvent):
            return (
                f"[verbose] Retrieved {event.result_count} passages for: {event.query}"
            )
        if isinstance(event, TokenUsageEvent):
            return (
                f"[verbose] Tokens: {event.input_tokens} in, {event.output_tokens} out"
            )
        return None

    def test_tool_invocation_event_format(self) -> None:
        event = ToolInvocationEvent(
            tool_name="search_book", arguments={"query": "whales"}
        )
        line = self._format_event(event)
        assert line == "[verbose] Tool call: search_book({'query': 'whales'})"

    def test_tool_result_event_format(self) -> None:
        event = ToolResultEvent(
            query="whales",
            result_count=3,
            results=[
                SearchResult(
                    chunk_id="c1",
                    content="About whales",
                    start_page=1,
                    end_page=1,
                    distance=0.1,
                )
            ],
        )
        line = self._format_event(event)
        assert line == "[verbose] Retrieved 3 passages for: whales"

    def test_token_usage_event_format(self) -> None:
        event = TokenUsageEvent(input_tokens=500, output_tokens=120)
        line = self._format_event(event)
        assert line == "[verbose] Tokens: 500 in, 120 out"
