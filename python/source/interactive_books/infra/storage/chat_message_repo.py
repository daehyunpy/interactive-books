import sqlite3
from datetime import datetime, timezone

from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.domain.protocols import (
    ChatMessageRepository as ChatMessageRepositoryPort,
)
from interactive_books.infra.storage.database import Database

_COLUMNS = "id, conversation_id, role, content, created_at"


class ChatMessageRepository(ChatMessageRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def save(self, message: ChatMessage) -> None:
        self._conn.execute(
            f"""
            INSERT INTO chat_messages ({_COLUMNS})
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.conversation_id,
                message.role.value,
                message.content,
                message.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_conversation(self, conversation_id: str) -> list[ChatMessage]:
        cursor = self._conn.execute(
            f"SELECT {_COLUMNS} FROM chat_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        )
        return [self._row_to_message(row) for row in cursor.fetchall()]

    def delete_by_conversation(self, conversation_id: str) -> None:
        self._conn.execute(
            "DELETE FROM chat_messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_message(row: sqlite3.Row | tuple) -> ChatMessage:  # type: ignore[type-arg]
        return ChatMessage(
            id=row[0],
            conversation_id=row[1],
            role=MessageRole(row[2]),
            content=row[3],
            created_at=datetime.fromisoformat(row[4]).replace(tzinfo=timezone.utc),
        )
