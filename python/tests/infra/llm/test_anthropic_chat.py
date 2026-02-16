from unittest.mock import MagicMock, patch

import pytest
from interactive_books.domain.errors import LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.infra.llm.anthropic import ChatProvider


class TestModelName:
    def test_returns_configured_model(self) -> None:
        provider = ChatProvider(api_key="test-key")

        assert provider.model_name == "claude-sonnet-4-5-20250514"


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

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}
        error = APIError(
            message="Internal server error",
            request=MagicMock(),
            body=None,
        )

        with patch.object(provider._client.messages, "create", side_effect=error):
            with pytest.raises(LLMError) as exc_info:
                provider.chat([PromptMessage(role="user", content="Hi")])

        assert exc_info.value.code == LLMErrorCode.API_CALL_FAILED
