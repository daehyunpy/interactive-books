from collections.abc import Callable

from interactive_books.domain.chat import MessageRole
from interactive_books.domain.chat_event import (
    ChatEvent,
    TokenUsageEvent,
    ToolInvocationEvent,
    ToolResultEvent,
)
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import (
    ChatResponse,
    TokenUsage,
    ToolDefinition,
    ToolInvocation,
)
from interactive_books.infra.retrieval.tool_use import RetrievalStrategy


def _search_tool() -> ToolDefinition:
    return ToolDefinition(
        name="search_book",
        description="Search",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
    )


class FakeChatProvider:
    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    @property
    def model_name(self) -> str:
        return "fake"

    def chat(self, messages: list[PromptMessage]) -> str:
        return ""

    def chat_with_tools(
        self, messages: list[PromptMessage], tools: list[ToolDefinition]
    ) -> ChatResponse:
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def _make_search_fn(
    results: list[SearchResult] | None = None,
) -> Callable[[str], list[SearchResult]]:
    captured_queries: list[str] = []

    def search_fn(query: str) -> list[SearchResult]:
        captured_queries.append(query)
        return results or []

    search_fn.captured_queries = captured_queries  # type: ignore[attr-defined]
    return search_fn


class TestToolUseStrategyDirectReply:
    def test_text_only_response_no_search(self) -> None:
        provider = FakeChatProvider([ChatResponse(text="The answer is clear.")])
        strategy = RetrievalStrategy()
        search_fn = _make_search_fn()

        text, new_messages = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Hello")],
            [_search_tool()],
            search_fn,
        )

        assert text == "The answer is clear."
        assert new_messages == []
        assert search_fn.captured_queries == []  # type: ignore[attr-defined]


class TestToolUseStrategyRetrieveAndReply:
    def test_single_tool_invocation_then_text(self) -> None:
        provider = FakeChatProvider(
            [
                ChatResponse(
                    tool_invocations=[
                        ToolInvocation(
                            tool_name="search_book",
                            tool_use_id="tu_1",
                            arguments={"query": "chapter 3"},
                        )
                    ]
                ),
                ChatResponse(text="Chapter 3 is about X."),
            ]
        )
        strategy = RetrievalStrategy()
        results = [
            SearchResult(
                chunk_id="c1",
                content="Chapter 3 content.",
                start_page=30,
                end_page=35,
                distance=0.1,
            )
        ]
        search_fn = _make_search_fn(results)

        text, new_messages = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Tell me about chapter 3")],
            [_search_tool()],
            search_fn,
        )

        assert text == "Chapter 3 is about X."
        assert len(new_messages) == 1
        assert new_messages[0].role == MessageRole.TOOL_RESULT
        assert "[Pages 30-35]" in new_messages[0].content
        assert search_fn.captured_queries == ["chapter 3"]  # type: ignore[attr-defined]


class TestToolUseStrategyMaxIterations:
    def test_stops_after_max_iterations(self) -> None:
        invocation = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_1",
            arguments={"query": "q"},
        )
        provider = FakeChatProvider(
            [
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(text="Final answer after max iterations."),
            ]
        )
        strategy = RetrievalStrategy()

        text, new_messages = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Q")],
            [_search_tool()],
            _make_search_fn(),
        )

        assert text == "Final answer after max iterations."
        assert len(new_messages) == 3

    def test_returns_nonempty_text_when_all_iterations_yield_tool_calls(self) -> None:
        """Reproduces bug: LLM never produces text, only tool calls on every
        iteration (including the final call after the loop). The strategy
        should never return an empty assistant response."""
        invocation = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_1",
            arguments={"query": "what did I ask?"},
        )
        # 3 loop iterations + 1 final call — all return tool invocations, no text
        provider = FakeChatProvider(
            [
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
            ]
        )
        strategy = RetrievalStrategy()

        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="what did I ask?")],
            [_search_tool()],
            _make_search_fn([]),
        )

        assert text != "", "Assistant response must not be empty"

    def test_returns_nonempty_text_when_final_response_has_no_text(self) -> None:
        """Reproduces bug: LLM exhausts tool iterations, then the final call
        returns text=None with no tool invocations (end_turn with empty content)."""
        invocation = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_1",
            arguments={"query": "tell me about julia"},
        )
        provider = FakeChatProvider(
            [
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(text=None),  # final call returns no text
            ]
        )
        strategy = RetrievalStrategy()

        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="tell me about julia")],
            [_search_tool()],
            _make_search_fn([]),
        )

        assert text != "", "Assistant response must not be empty"

    def test_returns_nonempty_text_when_results_are_irrelevant(self) -> None:
        """Reproduces bug: search returns results but they're irrelevant
        (e.g., early-book passages for a question about the ending).
        The LLM keeps retrying and never produces text."""
        invocation = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_1",
            arguments={"query": "what happens to Winston at the end"},
        )
        irrelevant_results = [
            SearchResult(
                chunk_id="c1",
                content="dust swirled in the air and the willow-herb straggled",
                start_page=6,
                end_page=8,
                distance=0.8,
            ),
            SearchResult(
                chunk_id="c2",
                content="an abstract, undirected emotion which could be switched",
                start_page=19,
                end_page=21,
                distance=0.7,
            ),
        ]
        # 3 loop iterations with irrelevant results + final call with no text
        provider = FakeChatProvider(
            [
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(tool_invocations=[invocation]),
                ChatResponse(text=None),
            ]
        )
        strategy = RetrievalStrategy()

        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="What happens to Winston at the end?")],
            [_search_tool()],
            _make_search_fn(irrelevant_results),
        )

        assert text != "", "Assistant response must not be empty"


class TestToolUseStrategyNoResults:
    def test_no_search_results_returns_no_passages_message(self) -> None:
        provider = FakeChatProvider(
            [
                ChatResponse(
                    tool_invocations=[
                        ToolInvocation(
                            tool_name="search_book",
                            tool_use_id="tu_1",
                            arguments={"query": "obscure topic"},
                        )
                    ]
                ),
                ChatResponse(text="I couldn't find anything."),
            ]
        )
        strategy = RetrievalStrategy()

        text, new_messages = strategy.execute(
            provider,
            [PromptMessage(role="user", content="What about obscure topic?")],
            [_search_tool()],
            _make_search_fn([]),
        )

        assert text == "I couldn't find anything."
        assert "No relevant passages" in new_messages[0].content


def _collect_events() -> tuple[list[ChatEvent], Callable[[ChatEvent], None]]:
    events: list[ChatEvent] = []
    return events, events.append


class TestToolUseStrategyEventEmission:
    def test_direct_reply_emits_token_usage_only(self) -> None:
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        provider = FakeChatProvider([ChatResponse(text="Answer.", usage=usage)])
        strategy = RetrievalStrategy()
        events, on_event = _collect_events()

        strategy.execute(
            provider,
            [PromptMessage(role="user", content="Hello")],
            [_search_tool()],
            _make_search_fn(),
            on_event=on_event,
        )

        assert len(events) == 1
        assert isinstance(events[0], TokenUsageEvent)
        assert events[0].input_tokens == 100
        assert events[0].output_tokens == 50

    def test_tool_use_emits_all_event_types(self) -> None:
        usage1 = TokenUsage(input_tokens=200, output_tokens=10)
        usage2 = TokenUsage(input_tokens=300, output_tokens=100)
        provider = FakeChatProvider(
            [
                ChatResponse(
                    tool_invocations=[
                        ToolInvocation(
                            tool_name="search_book",
                            tool_use_id="tu_1",
                            arguments={"query": "themes"},
                        )
                    ],
                    usage=usage1,
                ),
                ChatResponse(text="The themes are...", usage=usage2),
            ]
        )
        results = [
            SearchResult(
                chunk_id="c1",
                content="Theme text.",
                start_page=10,
                end_page=12,
                distance=0.1,
            )
        ]
        strategy = RetrievalStrategy()
        events, on_event = _collect_events()

        strategy.execute(
            provider,
            [PromptMessage(role="user", content="What are the themes?")],
            [_search_tool()],
            _make_search_fn(results),
            on_event=on_event,
        )

        # Expect: TokenUsage(1st call), ToolInvocation, ToolResult, TokenUsage(2nd call)
        assert len(events) == 4
        assert isinstance(events[0], TokenUsageEvent)
        assert isinstance(events[1], ToolInvocationEvent)
        assert events[1].tool_name == "search_book"
        assert events[1].arguments == {"query": "themes"}
        assert isinstance(events[2], ToolResultEvent)
        assert events[2].query == "themes"
        assert events[2].result_count == 1
        assert isinstance(events[3], TokenUsageEvent)

    def test_no_events_when_callback_is_none(self) -> None:
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        provider = FakeChatProvider([ChatResponse(text="Answer.", usage=usage)])
        strategy = RetrievalStrategy()

        # Should not raise — on_event defaults to None
        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Hello")],
            [_search_tool()],
            _make_search_fn(),
        )

        assert text == "Answer."

    def test_no_token_event_when_usage_is_none(self) -> None:
        provider = FakeChatProvider([ChatResponse(text="Answer.")])
        strategy = RetrievalStrategy()
        events, on_event = _collect_events()

        strategy.execute(
            provider,
            [PromptMessage(role="user", content="Hello")],
            [_search_tool()],
            _make_search_fn(),
            on_event=on_event,
        )

        assert len(events) == 0
