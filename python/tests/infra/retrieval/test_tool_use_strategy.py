from collections.abc import Callable

from interactive_books.domain.chat import MessageRole
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition, ToolInvocation
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
