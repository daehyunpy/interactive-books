import uuid
from collections.abc import Callable

from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.chat_event import (
    ChatEvent,
    TokenUsageEvent,
    ToolInvocationEvent,
    ToolResultEvent,
)
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition, ToolResult

MAX_TOOL_ITERATIONS = 3
EMPTY_RESPONSE_FALLBACK = (
    "I'm sorry, I wasn't able to find an answer. Could you try rephrasing your question?"
)
_PLACEHOLDER_CONVERSATION_ID = ""


class RetrievalStrategy:
    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]:
        current_messages = list(messages)
        new_chat_messages: list[ChatMessage] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = chat_provider.chat_with_tools(current_messages, tools)
            self._emit_token_usage(response, on_event)

            if not response.tool_invocations:
                text = response.text or EMPTY_RESPONSE_FALLBACK
                return text, new_chat_messages

            for invocation in response.tool_invocations:
                if on_event:
                    on_event(
                        ToolInvocationEvent(
                            tool_name=invocation.tool_name,
                            arguments=dict(invocation.arguments),
                        )
                    )

                assistant_msg = PromptMessage(
                    role="assistant",
                    content=response.text or "",
                    tool_invocations=[invocation],
                )
                current_messages.append(assistant_msg)

                handler = tool_handlers.get(invocation.tool_name)
                if handler is None:
                    tool_result_content = f"Unknown tool: {invocation.tool_name}"
                else:
                    result = handler(dict(invocation.arguments))
                    tool_result_content = result.formatted_text

                    search_results = [
                        r for r in result.results if isinstance(r, SearchResult)
                    ]
                    if on_event and search_results:
                        on_event(
                            ToolResultEvent(
                                query=result.query,
                                result_count=result.result_count,
                                results=search_results,
                            )
                        )

                tool_result_msg = PromptMessage(
                    role="tool_result",
                    content=tool_result_content,
                    tool_use_id=invocation.tool_use_id,
                )
                current_messages.append(tool_result_msg)

                new_chat_messages.append(
                    ChatMessage(
                        id=str(uuid.uuid4()),
                        conversation_id=_PLACEHOLDER_CONVERSATION_ID,
                        role=MessageRole.TOOL_RESULT,
                        content=tool_result_content,
                    )
                )

        current_messages.append(
            PromptMessage(
                role="user",
                content="Please answer based on the passages you have already retrieved.",
            )
        )
        final_response = chat_provider.chat_with_tools(current_messages, tools=[])
        self._emit_token_usage(final_response, on_event)
        text = final_response.text or EMPTY_RESPONSE_FALLBACK
        return text, new_chat_messages

    @staticmethod
    def _emit_token_usage(
        response: ChatResponse,
        on_event: Callable[[ChatEvent], None] | None,
    ) -> None:
        if on_event and response.usage:
            on_event(
                TokenUsageEvent(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            )
