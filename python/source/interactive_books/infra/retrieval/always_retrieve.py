from collections.abc import Callable
from pathlib import Path

from interactive_books.domain.chat import ChatMessage
from interactive_books.domain.chat_event import ChatEvent, ToolResultEvent
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ToolDefinition, ToolResult

NO_CONTEXT_MESSAGE = "No relevant passages found in the book for this query."


class RetrievalStrategy:
    def __init__(self, prompts_dir: Path) -> None:
        self._prompts_dir = prompts_dir

    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]:
        search_handler = tool_handlers.get("search_book")

        def search_fn(query: str) -> list[SearchResult]:
            if search_handler is None:
                return []
            result = search_handler({"query": query})
            return [r for r in result.results if isinstance(r, SearchResult)]

        query = self._reformulate_query(chat_provider, messages)
        results = search_fn(query)

        if on_event:
            on_event(
                ToolResultEvent(
                    query=query,
                    result_count=len(results),
                    results=results,
                )
            )

        context = self._format_context(results)

        augmented_messages = list(messages)
        last_user_idx = self._find_last_user_message_index(augmented_messages)
        if last_user_idx >= 0:
            original = augmented_messages[last_user_idx]
            augmented_messages[last_user_idx] = PromptMessage(
                role="user",
                content=f"Relevant passages:\n\n{context}\n\nUser question: {original.content}",
            )

        response_text = chat_provider.chat(augmented_messages)
        return response_text, []

    def _reformulate_query(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
    ) -> str:
        user_messages = [m for m in messages if m.role == "user"]
        if len(user_messages) <= 1:
            return user_messages[-1].content if user_messages else ""

        template = self._load_template("reformulation_prompt.md")

        history_lines = [
            f"{m.role}: {m.content}"
            for m in messages
            if m.role in ("user", "assistant")
        ]
        history = "\n".join(history_lines)

        latest = user_messages[-1].content
        prompt_text = template.format(history=history, message=latest)

        reformulated = chat_provider.chat(
            [PromptMessage(role="user", content=prompt_text)]
        )
        return reformulated.strip()

    def _load_template(self, filename: str) -> str:
        return (self._prompts_dir / filename).read_text().strip()

    @staticmethod
    def _format_context(results: list[SearchResult]) -> str:
        if not results:
            return NO_CONTEXT_MESSAGE
        passages = [
            f"[Pages {r.start_page}-{r.end_page}]:\n{r.content}" for r in results
        ]
        return "\n\n".join(passages)

    @staticmethod
    def _find_last_user_message_index(messages: list[PromptMessage]) -> int:
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].role == "user":
                return i
        return -1
