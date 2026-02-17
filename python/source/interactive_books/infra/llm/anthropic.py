from typing import Any

from anthropic import Anthropic, APIError
from anthropic.types import Message
from interactive_books.domain.errors import LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider as ChatProviderPort
from interactive_books.domain.tool import (
    ChatResponse,
    TokenUsage,
    ToolDefinition,
    ToolInvocation,
)

MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096


class ChatProvider(ChatProviderPort):
    def __init__(self, api_key: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = MODEL

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: list[PromptMessage]) -> str:
        response = self._call_api(messages)
        first_block = response.content[0]
        return first_block.text  # type: ignore[union-attr]

    def chat_with_tools(
        self,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
    ) -> ChatResponse:
        api_tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]
        response = self._call_api(messages, tools=api_tools)

        text = None
        invocations: list[ToolInvocation] = []

        for block in response.content:
            if block.type == "text":
                text = block.text
            elif block.type == "tool_use":
                invocations.append(
                    ToolInvocation(
                        tool_name=block.name,
                        tool_use_id=block.id,
                        arguments=dict(block.input)
                        if isinstance(block.input, dict)
                        else {},
                    )
                )

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return ChatResponse(text=text, tool_invocations=invocations, usage=usage)

    def _call_api(
        self,
        messages: list[PromptMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        system_text, api_messages = self._split_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": MAX_TOKENS,
            "messages": api_messages,
        }
        if system_text:
            kwargs["system"] = system_text
        if tools:
            kwargs["tools"] = tools

        try:
            return self._client.messages.create(**kwargs)
        except APIError as e:
            raise LLMError(
                LLMErrorCode.API_CALL_FAILED,
                f"Anthropic API error: {e}",
            ) from e

    @staticmethod
    def _split_messages(
        messages: list[PromptMessage],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        system_text: str | None = None
        api_messages: list[dict[str, Any]] = []

        for m in messages:
            if m.role == "system":
                system_text = m.content
            elif m.role == "tool_result" and m.tool_use_id:
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": m.tool_use_id,
                                "content": m.content,
                            }
                        ],
                    }
                )
            elif m.tool_invocations:
                content_blocks: list[dict[str, Any]] = []
                if m.content:
                    content_blocks.append({"type": "text", "text": m.content})
                for inv in m.tool_invocations:
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": inv.tool_use_id,
                            "name": inv.tool_name,
                            "input": inv.arguments,
                        }
                    )
                api_messages.append({"role": "assistant", "content": content_blocks})
            else:
                api_messages.append({"role": m.role, "content": m.content})

        return system_text, api_messages
