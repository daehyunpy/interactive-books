import uuid
from collections.abc import Callable
from pathlib import Path

from interactive_books.app.conversations import ManageConversationsUseCase
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.chat_event import ChatEvent
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import (
    BookRepository,
    ChatMessageRepository,
    ChatProvider,
    ConversationContextStrategy,
    ConversationRepository,
    RetrievalStrategy,
)
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ToolDefinition, ToolResult

SEARCH_BOOK_TOOL = ToolDefinition(
    name="search_book",
    description="Search the book for relevant passages matching a query. Use this when you need specific information from the book text.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A clear, self-contained search query. Resolve any pronouns or references from the conversation before searching.",
            }
        },
        "required": ["query"],
    },
)

SET_PAGE_TOOL = ToolDefinition(
    name="set_page",
    description="Update the reader's current page position in the book. Use this when the reader tells you what page they are on. Set to 0 to reset (show all content).",
    parameters={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": "The page number the reader is currently on. Must be 0 or positive. 0 resets the reading position.",
            }
        },
        "required": ["page"],
    },
)

NO_CONTEXT_MESSAGE = "No relevant passages found in the book for this query."


def _format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return NO_CONTEXT_MESSAGE
    passages = [
        f"[Pages {r.start_page}-{r.end_page}]:\n{r.content}" for r in results
    ]
    return "\n\n".join(passages)


def _parse_page_argument(arguments: dict[str, object]) -> int | None:
    try:
        return int(arguments.get("page", 0))  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def _error_tool_result(message: str) -> ToolResult:
    return ToolResult(formatted_text=f"Error: {message}", query="", result_count=0)


def _info_tool_result(message: str) -> ToolResult:
    return ToolResult(formatted_text=message, query="", result_count=0)


class ChatWithBookUseCase:
    def __init__(
        self,
        *,
        chat_provider: ChatProvider,
        retrieval_strategy: RetrievalStrategy,
        context_strategy: ConversationContextStrategy,
        search_use_case: SearchBooksUseCase,
        conversation_repo: ConversationRepository,
        message_repo: ChatMessageRepository,
        book_repo: BookRepository,
        prompts_dir: Path,
        on_event: Callable[[ChatEvent], None] | None = None,
        summary_context: str | None = None,
    ) -> None:
        self._chat = chat_provider
        self._retrieval = retrieval_strategy
        self._context = context_strategy
        self._search = search_use_case
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._book_repo = book_repo
        self._prompts_dir = prompts_dir
        self._on_event = on_event
        self._summary_context = summary_context

    def execute(self, conversation_id: str, user_message: str) -> str:
        conversation = self._conversation_repo.get(conversation_id)
        if conversation is None:
            raise BookError(
                BookErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' not found",
            )

        history = self._message_repo.get_by_conversation(conversation_id)
        context_window = self._context.build_context(history)

        system_prompt = self._load_template("conversation_system_prompt.md")

        if not history and self._summary_context:
            system_prompt += f"\n\nBook structure overview:\n{self._summary_context}"

        prompt_messages: list[PromptMessage] = [
            PromptMessage(role="system", content=system_prompt),
            *[PromptMessage(role=msg.role.value, content=msg.content) for msg in context_window],
            PromptMessage(role="user", content=user_message),
        ]

        book_id = conversation.book_id

        def search_book_handler(arguments: dict[str, object]) -> ToolResult:
            query = str(arguments.get("query", ""))
            results = self._search.execute(book_id, query)
            formatted = _format_search_results(results)
            return ToolResult(
                formatted_text=formatted,
                query=query,
                result_count=len(results),
                results=list(results),
            )

        def set_page_handler(arguments: dict[str, object]) -> ToolResult:
            page = _parse_page_argument(arguments)
            if page is None:
                return _error_tool_result("invalid page number — must be a whole number")

            book = self._book_repo.get(book_id)
            if book is None:
                return _error_tool_result(f"book not found ({book_id})")

            try:
                book.set_current_page(page)
            except BookError as e:
                return _error_tool_result(e.message)

            self._book_repo.save(book)

            if page == 0:
                return _info_tool_result(
                    "Reading position reset. All content is now available."
                )
            return _info_tool_result(f"Reading position set to page {page}.")

        tool_handlers = {
            "search_book": search_book_handler,
            "set_page": set_page_handler,
        }

        response_text, new_messages = self._retrieval.execute(
            self._chat,
            prompt_messages,
            [SEARCH_BOOK_TOOL, SET_PAGE_TOOL],
            tool_handlers,
            on_event=self._on_event,
        )

        user_chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )
        self._message_repo.save(user_chat_message)

        for msg in new_messages:
            self._message_repo.save(
                ChatMessage(
                    id=msg.id,
                    conversation_id=conversation_id,
                    role=msg.role,
                    content=msg.content,
                )
            )

        assistant_chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
        )
        self._message_repo.save(assistant_chat_message)

        if not history:
            auto_title = ManageConversationsUseCase.auto_title(user_message)
            conversation.rename(auto_title)
            self._conversation_repo.save(conversation)

        return response_text

    def _load_template(self, filename: str) -> str:
        return (self._prompts_dir / filename).read_text().strip()
