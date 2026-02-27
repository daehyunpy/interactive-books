from collections.abc import Callable
from pathlib import Path

import pytest
from interactive_books.domain.chat_event import ChatEvent, ToolResultEvent
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition, ToolResult
from interactive_books.infra.retrieval.always_retrieve import RetrievalStrategy

NO_CONTEXT_MESSAGE = "No relevant passages found in the book for this query."


class FakeChatProvider:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._call_count = 0
        self.chat_calls: list[list[PromptMessage]] = []

    @property
    def model_name(self) -> str:
        return "fake"

    def chat(self, messages: list[PromptMessage]) -> str:
        self.chat_calls.append(messages)
        response = self._responses[self._call_count]
        self._call_count += 1
        return response

    def chat_with_tools(
        self, messages: list[PromptMessage], tools: list[ToolDefinition]
    ) -> ChatResponse:
        return ChatResponse(text="")


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    (tmp_path / "reformulation_prompt.md").write_text(
        "Conversation:\n{history}\n\nLatest message: {message}\n\nReformulated query:"
    )
    return tmp_path


class FakeSearchHandler:
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.captured_queries: list[str] = []
        self._results = results or []

    def __call__(self, arguments: dict[str, object]) -> ToolResult:
        query = str(arguments.get("query", ""))
        self.captured_queries.append(query)
        if not self._results:
            formatted = NO_CONTEXT_MESSAGE
        else:
            formatted = "\n\n".join(
                f"[Pages {r.start_page}-{r.end_page}]:\n{r.content}"
                for r in self._results
            )
        return ToolResult(
            formatted_text=formatted,
            query=query,
            result_count=len(self._results),
            results=list(self._results),
        )

    def as_handlers(self) -> dict[str, Callable[[dict[str, object]], ToolResult]]:
        return {"search_book": self}


class TestAlwaysRetrieveSingleTurn:
    def test_single_turn_uses_original_query(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["The book says X."])
        strategy = RetrievalStrategy(prompts_dir)
        search = FakeSearchHandler([
            SearchResult(
                chunk_id="c1",
                content="Some content.",
                start_page=1,
                end_page=5,
                distance=0.1,
            )
        ])

        text, new_messages = strategy.execute(
            provider,
            [
                PromptMessage(role="system", content="You are helpful."),
                PromptMessage(role="user", content="What is chapter 1 about?"),
            ],
            [],
            search.as_handlers(),
        )

        assert text == "The book says X."
        assert new_messages == []
        assert search.captured_queries == ["What is chapter 1 about?"]


class TestAlwaysRetrieveMultiTurn:
    def test_multi_turn_reformulates_query(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(
            ["reformulated: What is the main theme of chapter 3?", "The theme is Y."]
        )
        strategy = RetrievalStrategy(prompts_dir)

        text, _ = strategy.execute(
            provider,
            [
                PromptMessage(role="user", content="Tell me about chapter 3"),
                PromptMessage(role="assistant", content="Chapter 3 is interesting."),
                PromptMessage(role="user", content="What is its main theme?"),
            ],
            [],
            FakeSearchHandler().as_handlers(),
        )

        assert text == "The theme is Y."
        assert len(provider.chat_calls) == 2


class TestAlwaysRetrieveContextFormatting:
    def test_no_results_uses_no_context_message(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["I don't know."])
        strategy = RetrievalStrategy(prompts_dir)

        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Obscure question")],
            [],
            FakeSearchHandler([]).as_handlers(),
        )

        assert text == "I don't know."
        last_call = provider.chat_calls[-1]
        user_msg = [m for m in last_call if m.role == "user"][-1]
        assert "No relevant passages" in user_msg.content


class TestAlwaysRetrieveEventEmission:
    def test_emits_tool_result_event(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["The answer."])
        strategy = RetrievalStrategy(prompts_dir)
        events: list[ChatEvent] = []

        strategy.execute(
            provider,
            [PromptMessage(role="user", content="Question?")],
            [],
            FakeSearchHandler([
                SearchResult(
                    chunk_id="c1",
                    content="Content.",
                    start_page=1,
                    end_page=3,
                    distance=0.1,
                )
            ]).as_handlers(),
            on_event=events.append,
        )

        assert len(events) == 1
        assert isinstance(events[0], ToolResultEvent)
        assert events[0].query == "Question?"
        assert events[0].result_count == 1

    def test_no_events_when_callback_is_none(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["The answer."])
        strategy = RetrievalStrategy(prompts_dir)

        # Should not raise
        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Question?")],
            [],
            FakeSearchHandler().as_handlers(),
        )

        assert text == "The answer."
