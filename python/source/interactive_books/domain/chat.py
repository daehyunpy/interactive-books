from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from interactive_books.domain._time import utc_now


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    id: str
    book_id: str
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=utc_now)
