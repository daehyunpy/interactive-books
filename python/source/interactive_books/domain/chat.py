from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ChatMessage:
    id: str
    book_id: str
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=_utc_now)
