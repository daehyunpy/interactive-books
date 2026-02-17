import uuid

from interactive_books.domain.conversation import Conversation
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import BookRepository, ConversationRepository

AUTO_TITLE_MAX_LENGTH = 60


class ManageConversationsUseCase:
    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository,
        book_repo: BookRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._book_repo = book_repo

    def create(self, book_id: str, title: str | None = None) -> Conversation:
        book = self._book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book '{book_id}' not found")

        effective_title = title or "New conversation"
        conversation = Conversation(
            id=str(uuid.uuid4()),
            book_id=book_id,
            title=effective_title,
        )
        self._conversation_repo.save(conversation)
        return conversation

    def list_by_book(self, book_id: str) -> list[Conversation]:
        return self._conversation_repo.get_by_book(book_id)

    def rename(self, conversation_id: str, title: str) -> Conversation:
        conversation = self._conversation_repo.get(conversation_id)
        if conversation is None:
            raise BookError(
                BookErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' not found",
            )
        conversation.rename(title)
        self._conversation_repo.save(conversation)
        return conversation

    def delete(self, conversation_id: str) -> None:
        conversation = self._conversation_repo.get(conversation_id)
        if conversation is None:
            raise BookError(
                BookErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' not found",
            )
        self._conversation_repo.delete(conversation_id)

    @staticmethod
    def auto_title(first_message: str) -> str:
        title = first_message.strip()
        if len(title) > AUTO_TITLE_MAX_LENGTH:
            title = title[:AUTO_TITLE_MAX_LENGTH].rsplit(" ", 1)[0] + "..."
        return title or "New conversation"
