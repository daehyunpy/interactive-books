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
from interactive_books.domain.tool import ChatResponse, ToolDefinition, ToolInvocation

MAX_TOOL_ITERATIONS = 3
NO_CONTEXT_MESSAGE = "No relevant passages found in the book for this query."
_PLACEHOLDER_CONVERSATION_ID = ""


class RetrievalStrategy:
    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        search_fn: Callable[[str], list[SearchResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]:
        current_messages = list(messages)
        new_chat_messages: list[ChatMessage] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = chat_provider.chat_with_tools(current_messages, tools)
            self._emit_token_usage(response, on_event)

            if not response.tool_invocations:
                return response.text or "", new_chat_messages

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

                query = str(invocation.arguments.get("query", ""))
                results = self._execute_tool(invocation, search_fn)

                if on_event:
                    on_event(
                        ToolResultEvent(
                            query=query,
                            result_count=len(results),
                            results=results,
                        )
                    )

                tool_result_content = self._format_results(results)

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

        final_response = chat_provider.chat_with_tools(current_messages, tools)
        self._emit_token_usage(final_response, on_event)
        return final_response.text or "", new_chat_messages

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

    @staticmethod
    def _execute_tool(
        invocation: ToolInvocation,
        search_fn: Callable[[str], list[SearchResult]],
    ) -> list[SearchResult]:
        query = str(invocation.arguments.get("query", ""))
        return search_fn(query)

    @staticmethod
    def _format_results(results: list[SearchResult]) -> str:
        if not results:
            return NO_CONTEXT_MESSAGE
        passages = [
            f"[Pages {r.start_page}-{r.end_page}]:\n{r.content}" for r in results
        ]
        return "\n\n".join(passages)
