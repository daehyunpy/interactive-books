from unittest.mock import MagicMock, patch

import pytest
from interactive_books.domain.errors import LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.tool import ToolDefinition, ToolInvocation
from interactive_books.infra.llm.anthropic import ChatProvider


class TestModelName:
    def test_returns_configured_model(self) -> None:
        provider = ChatProvider(api_key="test-key")

        assert provider.model_name == "claude-sonnet-4-5-20250929"


class TestChat:
    def test_successful_chat_returns_response_text(self) -> None:
        provider = ChatProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="The answer is 42.")]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            result = provider.chat(
                [
                    PromptMessage(role="user", content="What is the answer?"),
                ]
            )

        assert result == "The answer is 42."
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["messages"] == [
            {"role": "user", "content": "What is the answer?"}
        ]
        assert "system" not in call_kwargs

    def test_extracts_system_message(self) -> None:
        provider = ChatProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Sure.")]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            provider.chat(
                [
                    PromptMessage(role="system", content="You are helpful."),
                    PromptMessage(role="user", content="Hello"),
                ]
            )

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["system"] == "You are helpful."
        assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    def test_api_error_raises_llm_error(self) -> None:
        from anthropic import APIError

        provider = ChatProvider(api_key="test-key")

        error = APIError(
            message="Internal server error",
            request=MagicMock(),
            body=None,
        )

        with patch.object(provider._client.messages, "create", side_effect=error):
            with pytest.raises(LLMError) as exc_info:
                provider.chat([PromptMessage(role="user", content="Hi")])

        assert exc_info.value.code == LLMErrorCode.API_CALL_FAILED


def _search_tool() -> ToolDefinition:
    return ToolDefinition(
        name="search_book",
        description="Search the book",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )


class TestChatWithTools:
    def test_text_only_response(self) -> None:
        provider = ChatProvider(api_key="test-key")
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "No search needed."
        mock_response = MagicMock()
        mock_response.content = [text_block]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            result = provider.chat_with_tools(
                [PromptMessage(role="user", content="Hello")],
                [_search_tool()],
            )

        assert result.text == "No search needed."
        assert result.tool_invocations == []
        call_kwargs = mock_create.call_args.kwargs
        assert len(call_kwargs["tools"]) == 1
        assert call_kwargs["tools"][0]["name"] == "search_book"

    def test_tool_invocation_response(self) -> None:
        provider = ChatProvider(api_key="test-key")
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "search_book"
        tool_block.id = "tu_abc123"
        tool_block.input = {"query": "chapter 3 themes"}
        mock_response = MagicMock()
        mock_response.content = [tool_block]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ):
            result = provider.chat_with_tools(
                [PromptMessage(role="user", content="Tell me about chapter 3")],
                [_search_tool()],
            )

        assert result.text is None
        assert len(result.tool_invocations) == 1
        assert result.tool_invocations[0].tool_name == "search_book"
        assert result.tool_invocations[0].tool_use_id == "tu_abc123"
        assert result.tool_invocations[0].arguments == {"query": "chapter 3 themes"}

    def test_mixed_text_and_tool_response(self) -> None:
        provider = ChatProvider(api_key="test-key")
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Let me search for that."
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "search_book"
        tool_block.id = "tu_xyz"
        tool_block.input = {"query": "main character"}
        mock_response = MagicMock()
        mock_response.content = [text_block, tool_block]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ):
            result = provider.chat_with_tools(
                [PromptMessage(role="user", content="Who is the main character?")],
                [_search_tool()],
            )

        assert result.text == "Let me search for that."
        assert len(result.tool_invocations) == 1

    def test_api_error_raises_llm_error(self) -> None:
        from anthropic import APIError

        provider = ChatProvider(api_key="test-key")
        error = APIError(
            message="Rate limited",
            request=MagicMock(),
            body=None,
        )

        with patch.object(provider._client.messages, "create", side_effect=error):
            with pytest.raises(LLMError) as exc_info:
                provider.chat_with_tools(
                    [PromptMessage(role="user", content="Hi")],
                    [_search_tool()],
                )

        assert exc_info.value.code == LLMErrorCode.API_CALL_FAILED

    def test_tool_result_message_formatting(self) -> None:
        provider = ChatProvider(api_key="test-key")
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Based on the passage..."
        mock_response = MagicMock()
        mock_response.content = [text_block]

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            provider.chat_with_tools(
                [
                    PromptMessage(role="user", content="What about chapter 3?"),
                    PromptMessage(
                        role="assistant",
                        content="",
                        tool_invocations=[
                            ToolInvocation(
                                tool_name="search_book",
                                tool_use_id="tu_1",
                                arguments={"query": "chapter 3"},
                            )
                        ],
                    ),
                    PromptMessage(
                        role="tool_result",
                        content="[Pages 30-35]: Chapter 3 discusses...",
                        tool_use_id="tu_1",
                    ),
                ],
                [_search_tool()],
            )

        call_kwargs = mock_create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "user", "content": "What about chapter 3?"}
        # Assistant message with tool_use block
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"][0]["type"] == "tool_use"
        assert messages[1]["content"][0]["id"] == "tu_1"
        # Tool result message
        assert messages[2]["role"] == "user"
        assert messages[2]["content"][0]["type"] == "tool_result"
        assert messages[2]["content"][0]["tool_use_id"] == "tu_1"
