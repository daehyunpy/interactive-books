from collections.abc import Callable
from pathlib import Path

import pytest
from interactive_books.domain.chat_event import ChatEvent, ToolResultEvent
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition
from interactive_books.infra.retrieval.always_retrieve import RetrievalStrategy


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


def _make_search_fn(
    results: list[SearchResult] | None = None,
) -> Callable[[str], list[SearchResult]]:
    captured: list[str] = []

    def search_fn(query: str) -> list[SearchResult]:
        captured.append(query)
        return results or []

    search_fn.captured_queries = captured  # type: ignore[attr-defined]
    return search_fn


class TestAlwaysRetrieveSingleTurn:
    def test_single_turn_uses_original_query(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["The book says X."])
        strategy = RetrievalStrategy(prompts_dir)
        results = [
            SearchResult(
                chunk_id="c1",
                content="Some content.",
                start_page=1,
                end_page=5,
                distance=0.1,
            )
        ]
        search_fn = _make_search_fn(results)

        text, new_messages = strategy.execute(
            provider,
            [
                PromptMessage(role="system", content="You are helpful."),
                PromptMessage(role="user", content="What is chapter 1 about?"),
            ],
            [],
            search_fn,
        )

        assert text == "The book says X."
        assert new_messages == []
        assert search_fn.captured_queries == ["What is chapter 1 about?"]  # type: ignore[attr-defined]


class TestAlwaysRetrieveMultiTurn:
    def test_multi_turn_reformulates_query(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(
            ["reformulated: What is the main theme of chapter 3?", "The theme is Y."]
        )
        strategy = RetrievalStrategy(prompts_dir)
        search_fn = _make_search_fn()

        text, _ = strategy.execute(
            provider,
            [
                PromptMessage(role="user", content="Tell me about chapter 3"),
                PromptMessage(role="assistant", content="Chapter 3 is interesting."),
                PromptMessage(role="user", content="What is its main theme?"),
            ],
            [],
            search_fn,
        )

        assert text == "The theme is Y."
        assert len(provider.chat_calls) == 2


class TestAlwaysRetrieveContextFormatting:
    def test_no_results_uses_no_context_message(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["I don't know."])
        strategy = RetrievalStrategy(prompts_dir)
        search_fn = _make_search_fn([])

        text, _ = strategy.execute(
            provider,
            [PromptMessage(role="user", content="Obscure question")],
            [],
            search_fn,
        )

        assert text == "I don't know."
        last_call = provider.chat_calls[-1]
        user_msg = [m for m in last_call if m.role == "user"][-1]
        assert "No relevant passages" in user_msg.content


class TestAlwaysRetrieveEventEmission:
    def test_emits_tool_result_event(self, prompts_dir: Path) -> None:
        provider = FakeChatProvider(["The answer."])
        strategy = RetrievalStrategy(prompts_dir)
        results = [
            SearchResult(
                chunk_id="c1",
                content="Content.",
                start_page=1,
                end_page=3,
                distance=0.1,
            )
        ]
        search_fn = _make_search_fn(results)
        events: list[ChatEvent] = []

        strategy.execute(
            provider,
            [PromptMessage(role="user", content="Question?")],
            [],
            search_fn,
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
            _make_search_fn(),
        )

        assert text == "The answer."
