import sqlite3
from datetime import datetime, timezone

from interactive_books.domain.chunk import Chunk
from interactive_books.infra.storage.database import Database


class SqliteChunkRepository:
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def save_chunks(self, book_id: str, chunks: list[Chunk]) -> None:
        self._conn.executemany(
            """
            INSERT INTO chunks (id, book_id, content, start_page, end_page, chunk_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.id,
                    chunk.book_id,
                    chunk.content,
                    chunk.start_page,
                    chunk.end_page,
                    chunk.chunk_index,
                    chunk.created_at.isoformat(),
                )
                for chunk in chunks
            ],
        )
        self._conn.commit()

    def get_by_book(self, book_id: str) -> list[Chunk]:
        cursor = self._conn.execute(
            "SELECT id, book_id, content, start_page, end_page, chunk_index, created_at FROM chunks WHERE book_id = ? ORDER BY chunk_index",
            (book_id,),
        )
        return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def get_up_to_page(self, book_id: str, page: int) -> list[Chunk]:
        cursor = self._conn.execute(
            "SELECT id, book_id, content, start_page, end_page, chunk_index, created_at FROM chunks WHERE book_id = ? AND start_page <= ? ORDER BY chunk_index",
            (book_id, page),
        )
        return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def delete_by_book(self, book_id: str) -> None:
        self._conn.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row | tuple) -> Chunk:  # type: ignore[type-arg]
        return Chunk(
            id=row[0],
            book_id=row[1],
            content=row[2],
            start_page=row[3],
            end_page=row[4],
            chunk_index=row[5],
            created_at=datetime.fromisoformat(row[6]).replace(tzinfo=timezone.utc),
        )
