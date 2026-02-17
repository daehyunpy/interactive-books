from interactive_books.domain.chat import ChatMessage

DEFAULT_MAX_MESSAGES = 20


class ConversationContextStrategy:
    def __init__(self, max_messages: int = DEFAULT_MAX_MESSAGES) -> None:
        self._max_messages = max_messages

    def build_context(self, history: list[ChatMessage]) -> list[ChatMessage]:
        return list(history[-self._max_messages :])
