import uuid
from pathlib import Path

from interactive_books.app.conversations import ManageConversationsUseCase
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import (
    ChatMessageRepository,
    ChatProvider,
    ConversationContextStrategy,
    ConversationRepository,
    RetrievalStrategy,
)
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ToolDefinition

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
        prompts_dir: Path,
    ) -> None:
        self._chat = chat_provider
        self._retrieval = retrieval_strategy
        self._context = context_strategy
        self._search = search_use_case
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._prompts_dir = prompts_dir

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

        prompt_messages: list[PromptMessage] = [
            PromptMessage(role="system", content=system_prompt)
        ]
        for msg in context_window:
            prompt_messages.append(
                PromptMessage(role=msg.role.value, content=msg.content)
            )
        prompt_messages.append(PromptMessage(role="user", content=user_message))

        book_id = conversation.book_id

        def search_fn(query: str) -> list[SearchResult]:
            return self._search.execute(book_id, query)

        response_text, new_messages = self._retrieval.execute(
            self._chat, prompt_messages, [SEARCH_BOOK_TOOL], search_fn
        )

        user_chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )
        self._message_repo.save(user_chat_message)

        for msg in new_messages:
            persisted_msg = ChatMessage(
                id=msg.id,
                conversation_id=conversation_id,
                role=msg.role,
                content=msg.content,
            )
            self._message_repo.save(persisted_msg)

        assistant_chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
        )
        self._message_repo.save(assistant_chat_message)

        if len(history) == 0:
            auto_title = ManageConversationsUseCase.auto_title(user_message)
            conversation.rename(auto_title)
            self._conversation_repo.save(conversation)

        return response_text

    def _load_template(self, filename: str) -> str:
        return (self._prompts_dir / filename).read_text().strip()
