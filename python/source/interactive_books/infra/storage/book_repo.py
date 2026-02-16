import sqlite3
from datetime import datetime, timezone

from interactive_books.domain.book import Book, BookStatus
from interactive_books.infra.storage.database import Database


_BOOK_COLUMNS = "id, title, status, current_page, embedding_provider, embedding_dimension, created_at, updated_at"


class BookRepository:
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def save(self, book: Book) -> None:
        self._conn.execute(
            f"""
            INSERT OR REPLACE INTO books ({_BOOK_COLUMNS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book.id,
                book.title,
                book.status.value,
                book.current_page,
                book.embedding_provider,
                book.embedding_dimension,
                book.created_at.isoformat(),
                book.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, book_id: str) -> Book | None:
        cursor = self._conn.execute(
            f"SELECT {_BOOK_COLUMNS} FROM books WHERE id = ?",
            (book_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_book(row)

    def get_all(self) -> list[Book]:
        cursor = self._conn.execute(f"SELECT {_BOOK_COLUMNS} FROM books")
        return [self._row_to_book(row) for row in cursor.fetchall()]

    def delete(self, book_id: str) -> None:
        self._conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_book(row: sqlite3.Row | tuple) -> Book:  # type: ignore[type-arg]
        return Book(
            id=row[0],
            title=row[1],
            status=BookStatus(row[2]),
            current_page=row[3],
            embedding_provider=row[4],
            embedding_dimension=row[5],
            created_at=datetime.fromisoformat(row[6]).replace(tzinfo=timezone.utc),
            updated_at=datetime.fromisoformat(row[7]).replace(tzinfo=timezone.utc),
        )
