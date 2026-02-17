import sqlite3
from datetime import datetime, timezone

from interactive_books.domain.conversation import Conversation
from interactive_books.domain.protocols import (
    ConversationRepository as ConversationRepositoryPort,
)
from interactive_books.infra.storage.database import Database

_COLUMNS = "id, book_id, title, created_at"


class ConversationRepository(ConversationRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def save(self, conversation: Conversation) -> None:
        self._conn.execute(
            f"""
            INSERT INTO conversations ({_COLUMNS})
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title
            """,
            (
                conversation.id,
                conversation.book_id,
                conversation.title,
                conversation.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, conversation_id: str) -> Conversation | None:
        cursor = self._conn.execute(
            f"SELECT {_COLUMNS} FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_conversation(row)

    def get_by_book(self, book_id: str) -> list[Conversation]:
        cursor = self._conn.execute(
            f"SELECT {_COLUMNS} FROM conversations WHERE book_id = ? ORDER BY created_at DESC",
            (book_id,),
        )
        return [self._row_to_conversation(row) for row in cursor.fetchall()]

    def delete(self, conversation_id: str) -> None:
        self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_conversation(row: sqlite3.Row | tuple) -> Conversation:  # type: ignore[type-arg]
        return Conversation(
            id=row[0],
            book_id=row[1],
            title=row[2],
            created_at=datetime.fromisoformat(row[3]).replace(tzinfo=timezone.utc),
        )
