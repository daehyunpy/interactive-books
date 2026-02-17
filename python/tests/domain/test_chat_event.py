import pytest
from interactive_books.domain.chat_event import (
    ChatEvent,
    TokenUsageEvent,
    ToolInvocationEvent,
    ToolResultEvent,
)
from interactive_books.domain.search_result import SearchResult


class TestToolInvocationEvent:
    def test_create(self) -> None:
        event = ToolInvocationEvent(
            tool_name="search_book",
            arguments={"query": "protagonist"},
        )
        assert event.tool_name == "search_book"
        assert event.arguments["query"] == "protagonist"

    def test_is_immutable(self) -> None:
        event = ToolInvocationEvent(tool_name="t", arguments={})
        with pytest.raises(AttributeError):
            event.tool_name = "other"  # type: ignore[misc]


class TestToolResultEvent:
    def test_create(self) -> None:
        results = [
            SearchResult(
                chunk_id="c1",
                content="Some text",
                start_page=1,
                end_page=2,
                distance=0.1,
            )
        ]
        event = ToolResultEvent(query="test", result_count=1, results=results)
        assert event.query == "test"
        assert event.result_count == 1
        assert len(event.results) == 1


class TestTokenUsageEvent:
    def test_create(self) -> None:
        event = TokenUsageEvent(input_tokens=100, output_tokens=50)
        assert event.input_tokens == 100
        assert event.output_tokens == 50

    def test_is_immutable(self) -> None:
        event = TokenUsageEvent(input_tokens=100, output_tokens=50)
        with pytest.raises(AttributeError):
            event.input_tokens = 200  # type: ignore[misc]


class TestChatEventTypeAlias:
    def test_all_event_types_are_chat_events(self) -> None:
        events: list[ChatEvent] = [
            ToolInvocationEvent(tool_name="t", arguments={}),
            ToolResultEvent(query="q", result_count=0, results=[]),
            TokenUsageEvent(input_tokens=0, output_tokens=0),
        ]
        assert len(events) == 3
