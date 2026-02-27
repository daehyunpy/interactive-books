from collections.abc import Callable
from pathlib import Path

import pytest
from interactive_books.app.chat import ChatWithBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.chat_event import ChatEvent
from interactive_books.domain.conversation import Conversation
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition, ToolResult

# ── Fakes ────────────────────────────────────────────────────────


class FakeConversationRepository:
    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self._store.get(conversation_id)

    def get_by_book(self, book_id: str) -> list[Conversation]:
        return [c for c in self._store.values() if c.book_id == book_id]

    def delete(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)


class FakeChatMessageRepository:
    def __init__(self) -> None:
        self._store: list[ChatMessage] = []

    def save(self, message: ChatMessage) -> None:
        self._store.append(message)

    def get_by_conversation(self, conversation_id: str) -> list[ChatMessage]:
        return [m for m in self._store if m.conversation_id == conversation_id]

    def delete_by_conversation(self, conversation_id: str) -> None:
        self._store = [m for m in self._store if m.conversation_id != conversation_id]


class FakeBookRepository:
    def __init__(self) -> None:
        self._store: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self._store[book.id] = book

    def get(self, book_id: str) -> Book | None:
        return self._store.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self._store.values())

    def delete(self, book_id: str) -> None:
        self._store.pop(book_id, None)


class FakeSearchBooksUseCase:
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self._results = results or []
        self.last_query: str | None = None

    def execute(self, book_id: str, query: str, top_k: int = 5) -> list[SearchResult]:
        self.last_query = query
        return self._results


class FakeRetrievalStrategy:
    """Returns a canned response text and optional intermediate messages."""

    def __init__(
        self,
        response_text: str = "Here is my answer.",
        intermediate_messages: list[ChatMessage] | None = None,
    ) -> None:
        self._response_text = response_text
        self._intermediate = intermediate_messages or []
        self.last_messages: list[PromptMessage] | None = None
        self.last_tools: list[ToolDefinition] | None = None
        self.last_tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]] | None = (
            None
        )
        self.last_on_event: Callable[[ChatEvent], None] | None = None

    def execute(
        self,
        chat_provider: object,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]:
        self.last_messages = messages
        self.last_tools = tools
        self.last_tool_handlers = tool_handlers
        self.last_on_event = on_event
        return self._response_text, self._intermediate


class FakeContextStrategy:
    def build_context(self, history: list[ChatMessage]) -> list[ChatMessage]:
        return history


class FakeChatProvider:
    @property
    def model_name(self) -> str:
        return "fake-model"

    def chat(self, messages: list[PromptMessage]) -> str:
        return ""

    def chat_with_tools(
        self, messages: list[PromptMessage], tools: list[ToolDefinition]
    ) -> ChatResponse:
        return ChatResponse(text="")


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    (tmp_path / "conversation_system_prompt.md").write_text(
        "You are a reading companion."
    )
    return tmp_path


@pytest.fixture
def conversation_repo() -> FakeConversationRepository:
    return FakeConversationRepository()


@pytest.fixture
def message_repo() -> FakeChatMessageRepository:
    return FakeChatMessageRepository()


def _seed_conversation(
    repo: FakeConversationRepository,
    *,
    conv_id: str = "conv-1",
    book_id: str = "book-1",
) -> Conversation:
    conv = Conversation(id=conv_id, book_id=book_id, title="Test conversation")
    repo.save(conv)
    return conv


def _make_use_case(
    *,
    conversation_repo: FakeConversationRepository,
    message_repo: FakeChatMessageRepository,
    prompts_dir: Path,
    retrieval: FakeRetrievalStrategy | None = None,
    context: FakeContextStrategy | None = None,
    search: FakeSearchBooksUseCase | None = None,
    chat: FakeChatProvider | None = None,
    book_repo: FakeBookRepository | None = None,
    on_event: Callable[[ChatEvent], None] | None = None,
) -> ChatWithBookUseCase:
    return ChatWithBookUseCase(
        chat_provider=chat or FakeChatProvider(),
        retrieval_strategy=retrieval or FakeRetrievalStrategy(),
        context_strategy=context or FakeContextStrategy(),
        search_use_case=search or FakeSearchBooksUseCase(),  # type: ignore[arg-type]
        conversation_repo=conversation_repo,  # type: ignore[arg-type]
        message_repo=message_repo,  # type: ignore[arg-type]
        book_repo=book_repo or FakeBookRepository(),  # type: ignore[arg-type]
        prompts_dir=prompts_dir,
        on_event=on_event,
    )


# ── Tests: Direct Reply (no retrieval) ──────────────────────────


class TestDirectReply:
    def test_returns_response_text(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy(response_text="The protagonist is Ishmael.")
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        result = uc.execute("conv-1", "Who is the main character?")

        assert result == "The protagonist is Ishmael."

    def test_passes_system_prompt_to_retrieval(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_messages is not None
        system_msg = retrieval.last_messages[0]
        assert system_msg.role == "system"
        assert "reading companion" in system_msg.content

    def test_passes_search_book_tool(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_tools is not None
        tool_names = [t.name for t in retrieval.last_tools]
        assert "search_book" in tool_names


# ── Tests: Retrieve-then-Reply ───────────────────────────────────


class TestRetrieveThenReply:
    def test_persists_intermediate_tool_result_messages(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        tool_msg = ChatMessage(
            id="tool-msg-1",
            conversation_id="",
            role=MessageRole.TOOL_RESULT,
            content="Passage about whales.",
        )
        retrieval = FakeRetrievalStrategy(
            response_text="Whales are central.",
            intermediate_messages=[tool_msg],
        )
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Tell me about whales")

        saved = message_repo.get_by_conversation("conv-1")
        roles = [m.role for m in saved]
        assert MessageRole.TOOL_RESULT in roles
        tool_saved = [m for m in saved if m.role == MessageRole.TOOL_RESULT][0]
        assert tool_saved.conversation_id == "conv-1"
        assert tool_saved.content == "Passage about whales."


# ── Tests: Message Persistence ───────────────────────────────────


class TestMessagePersistence:
    def test_persists_user_and_assistant_messages(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
        )

        uc.execute("conv-1", "What is the theme?")

        saved = message_repo.get_by_conversation("conv-1")
        assert len(saved) == 2
        assert saved[0].role == MessageRole.USER
        assert saved[0].content == "What is the theme?"
        assert saved[1].role == MessageRole.ASSISTANT
        assert saved[1].content == "Here is my answer."

    def test_message_order_user_tool_result_assistant(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        tool_msg = ChatMessage(
            id="tool-msg-1",
            conversation_id="",
            role=MessageRole.TOOL_RESULT,
            content="Retrieved passage.",
        )
        retrieval = FakeRetrievalStrategy(
            response_text="Answer based on passage.",
            intermediate_messages=[tool_msg],
        )
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Find this")

        saved = message_repo.get_by_conversation("conv-1")
        roles = [m.role for m in saved]
        assert roles == [
            MessageRole.USER,
            MessageRole.TOOL_RESULT,
            MessageRole.ASSISTANT,
        ]

    def test_all_messages_have_correct_conversation_id(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        tool_msg = ChatMessage(
            id="tool-1", conversation_id="", role=MessageRole.TOOL_RESULT, content="x"
        )
        retrieval = FakeRetrievalStrategy(intermediate_messages=[tool_msg])
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "question")

        for msg in message_repo.get_by_conversation("conv-1"):
            assert msg.conversation_id == "conv-1"


# ── Tests: Conversation Not Found ────────────────────────────────


class TestConversationNotFound:
    def test_raises_not_found_for_missing_conversation(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
        )

        with pytest.raises(BookError) as exc_info:
            uc.execute("nonexistent", "Hello")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


# ── Tests: Auto-Title on First Message ───────────────────────────


class TestAutoTitle:
    def test_auto_titles_conversation_on_first_message(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
        )

        uc.execute("conv-1", "What is the theme of the book?")

        conv = conversation_repo.get("conv-1")
        assert conv is not None
        assert conv.title == "What is the theme of the book?"

    def test_does_not_retitle_on_subsequent_messages(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        conv = _seed_conversation(conversation_repo)
        existing_msg = ChatMessage(
            id="prev-1",
            conversation_id="conv-1",
            role=MessageRole.USER,
            content="First question",
        )
        message_repo.save(existing_msg)

        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
        )

        uc.execute("conv-1", "Follow-up question")

        conv = conversation_repo.get("conv-1")
        assert conv is not None
        assert conv.title == "Test conversation"


# ── Tests: Context Strategy Integration ──────────────────────────


class TestContextIntegration:
    def test_history_messages_appear_in_prompt(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        prev = ChatMessage(
            id="prev-1",
            conversation_id="conv-1",
            role=MessageRole.USER,
            content="Earlier question",
        )
        message_repo.save(prev)

        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Follow-up")

        assert retrieval.last_messages is not None
        # system + history user + new user = 3 messages
        assert len(retrieval.last_messages) == 3
        assert retrieval.last_messages[1].content == "Earlier question"
        assert retrieval.last_messages[2].content == "Follow-up"


# ── Tests: Event Callback Passthrough ────────────────────────────


class TestEventCallbackPassthrough:
    def test_on_event_passed_to_retrieval_strategy(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        events: list[ChatEvent] = []
        callback = events.append
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            on_event=callback,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_on_event is callback

    def test_none_on_event_passed_when_not_provided(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_on_event is None


# ── Helpers for set_page tests ─────────────────────────────────


def _seed_book(
    repo: FakeBookRepository,
    *,
    book_id: str = "book-1",
    current_page: int = 0,
) -> Book:
    book = Book(id=book_id, title="Test Book", status=BookStatus.READY, current_page=current_page)
    repo.save(book)
    return book


def _invoke_set_page(
    retrieval: FakeRetrievalStrategy,
    arguments: dict[str, object],
) -> ToolResult:
    """Call the set_page handler captured by the fake retrieval strategy."""
    assert retrieval.last_tool_handlers is not None
    handler = retrieval.last_tool_handlers["set_page"]
    return handler(arguments)


# ── Tests: set_page Tool Registration ──────────────────────────


class TestSetPageToolRegistration:
    def test_set_page_tool_appears_in_tools_list(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        book_repo = FakeBookRepository()
        _seed_book(book_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_tools is not None
        tool_names = [t.name for t in retrieval.last_tools]
        assert "set_page" in tool_names

    def test_set_page_handler_registered(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        _seed_conversation(conversation_repo)
        book_repo = FakeBookRepository()
        _seed_book(book_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Hello")

        assert retrieval.last_tool_handlers is not None
        assert "set_page" in retrieval.last_tool_handlers


# ── Tests: set_page Happy Path ─────────────────────────────────


class TestSetPageHappyPath:
    def test_sets_page_on_book(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        book_repo = FakeBookRepository()
        _seed_book(book_repo, current_page=0)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        result = _invoke_set_page(retrieval, {"page": 42})

        book = book_repo.get("book-1")
        assert book is not None
        assert book.current_page == 42
        assert result.result_count == 0
        assert "42" in result.formatted_text

    def test_resets_page_to_zero(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        book_repo = FakeBookRepository()
        _seed_book(book_repo, current_page=50)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Reset page")
        result = _invoke_set_page(retrieval, {"page": 0})

        book = book_repo.get("book-1")
        assert book is not None
        assert book.current_page == 0
        assert "reset" in result.formatted_text.lower()


# ── Tests: set_page Coercion (Recommendation 3) ───────────────


class TestSetPageCoercion:
    def test_coerces_float_to_int(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        """LLMs send 50.0 for integer params because JSON has no int type."""
        book_repo = FakeBookRepository()
        _seed_book(book_repo)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        result = _invoke_set_page(retrieval, {"page": 50.0})

        book = book_repo.get("book-1")
        assert book is not None
        assert book.current_page == 50
        assert "50" in result.formatted_text

    def test_coerces_string_to_int(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        """Handles string page values gracefully."""
        book_repo = FakeBookRepository()
        _seed_book(book_repo)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        _invoke_set_page(retrieval, {"page": "50"})

        book = book_repo.get("book-1")
        assert book is not None
        assert book.current_page == 50


# ── Tests: set_page Error Handling (Recommendation 1) ──────────


class TestSetPageErrorHandling:
    def test_returns_error_for_negative_page(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        """Domain error caught and returned in ToolResult, not raised."""
        book_repo = FakeBookRepository()
        _seed_book(book_repo, current_page=10)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        result = _invoke_set_page(retrieval, {"page": -5})

        # Error returned in ToolResult, not raised
        assert "error" in result.formatted_text.lower() or "negative" in result.formatted_text.lower()
        # Book unchanged
        book = book_repo.get("book-1")
        assert book is not None
        assert book.current_page == 10

    def test_returns_error_for_non_numeric_page(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        """Non-numeric input caught and returned in ToolResult."""
        book_repo = FakeBookRepository()
        _seed_book(book_repo)
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        result = _invoke_set_page(retrieval, {"page": "fifty"})

        assert "error" in result.formatted_text.lower() or "invalid" in result.formatted_text.lower()


# ── Tests: set_page Book Not Found Guard (Recommendation 2) ───


class TestSetPageBookNotFound:
    def test_returns_error_when_book_missing(
        self,
        prompts_dir: Path,
        conversation_repo: FakeConversationRepository,
        message_repo: FakeChatMessageRepository,
    ) -> None:
        """Guard against book_repo.get() returning None."""
        book_repo = FakeBookRepository()
        # Seed conversation pointing to book-1, but do NOT seed the book
        _seed_conversation(conversation_repo)
        retrieval = FakeRetrievalStrategy()
        uc = _make_use_case(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=prompts_dir,
            retrieval=retrieval,
            book_repo=book_repo,
        )

        uc.execute("conv-1", "Set page")
        result = _invoke_set_page(retrieval, {"page": 10})

        assert "error" in result.formatted_text.lower() or "not found" in result.formatted_text.lower()
