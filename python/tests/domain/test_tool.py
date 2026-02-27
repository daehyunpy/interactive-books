import pytest
from interactive_books.domain.tool import (
    ChatResponse,
    TokenUsage,
    ToolDefinition,
    ToolInvocation,
    ToolResult,
)


class TestToolDefinition:
    def test_create_tool_definition(self) -> None:
        td = ToolDefinition(
            name="search_book",
            description="Search the book for relevant passages",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
        assert td.name == "search_book"
        assert td.description == "Search the book for relevant passages"
        assert td.parameters["type"] == "object"

    def test_tool_definition_is_immutable(self) -> None:
        td = ToolDefinition(name="t", description="d", parameters={})
        with pytest.raises(AttributeError):
            td.name = "other"  # type: ignore[misc]


class TestToolInvocation:
    def test_create_tool_invocation(self) -> None:
        ti = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_123",
            arguments={"query": "What is chapter 3 about?"},
        )
        assert ti.tool_name == "search_book"
        assert ti.tool_use_id == "tu_123"
        assert ti.arguments["query"] == "What is chapter 3 about?"

    def test_tool_invocation_is_immutable(self) -> None:
        ti = ToolInvocation(tool_name="t", tool_use_id="id", arguments={})
        with pytest.raises(AttributeError):
            ti.tool_name = "other"  # type: ignore[misc]


class TestChatResponse:
    def test_text_only_response(self) -> None:
        cr = ChatResponse(text="Here is the answer.")
        assert cr.text == "Here is the answer."
        assert cr.tool_invocations == []

    def test_tool_invocation_response(self) -> None:
        invocation = ToolInvocation(
            tool_name="search_book",
            tool_use_id="tu_456",
            arguments={"query": "chapter 3"},
        )
        cr = ChatResponse(tool_invocations=[invocation])
        assert cr.text is None
        assert len(cr.tool_invocations) == 1
        assert cr.tool_invocations[0].tool_name == "search_book"

    def test_defaults(self) -> None:
        cr = ChatResponse()
        assert cr.text is None
        assert cr.tool_invocations == []
        assert cr.usage is None

    def test_response_with_usage(self) -> None:
        usage = TokenUsage(input_tokens=1234, output_tokens=567)
        cr = ChatResponse(text="answer", usage=usage)
        assert cr.usage is not None
        assert cr.usage.input_tokens == 1234
        assert cr.usage.output_tokens == 567


class TestTokenUsage:
    def test_create_token_usage(self) -> None:
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

    def test_token_usage_is_immutable(self) -> None:
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        with pytest.raises(AttributeError):
            usage.input_tokens = 200  # type: ignore[misc]


class TestToolResult:
    def test_create_tool_result(self) -> None:
        tr = ToolResult(
            formatted_text="[Pages 1-5]: Content here",
            query="chapter 3",
            result_count=1,
            results=["fake_result"],
        )
        assert tr.formatted_text == "[Pages 1-5]: Content here"
        assert tr.query == "chapter 3"
        assert tr.result_count == 1
        assert len(tr.results) == 1

    def test_tool_result_defaults(self) -> None:
        tr = ToolResult(formatted_text="text", query="q", result_count=0)
        assert tr.results == []

    def test_tool_result_is_immutable(self) -> None:
        tr = ToolResult(formatted_text="text", query="q", result_count=0)
        with pytest.raises(AttributeError):
            tr.query = "other"  # type: ignore[misc]
