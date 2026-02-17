from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from interactive_books.domain._time import utc_now


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"


@dataclass(frozen=True)
class ChatMessage:
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=utc_now)
