import struct

from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.protocols import (
    EmbeddingRepository as EmbeddingRepositoryPort,
)
from interactive_books.infra.storage.database import Database


def _table_name(provider_name: str, dimension: int) -> str:
    return f"embeddings_{provider_name}_{dimension}"


def _serialize_f32(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


class EmbeddingRepository(EmbeddingRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def ensure_table(self, provider_name: str, dimension: int) -> None:
        table = _table_name(provider_name, dimension)
        self._conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING vec0(
                book_id text partition key,
                +chunk_id text,
                vector float[{dimension}]
            )
            """
        )

    def save_embeddings(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        embeddings: list[EmbeddingVector],
    ) -> None:
        table = _table_name(provider_name, dimension)
        self._conn.executemany(
            f"INSERT INTO {table}(book_id, chunk_id, vector) VALUES (?, ?, ?)",
            [(book_id, ev.chunk_id, _serialize_f32(ev.vector)) for ev in embeddings],
        )
        self._conn.commit()

    def delete_by_book(self, provider_name: str, dimension: int, book_id: str) -> None:
        table = _table_name(provider_name, dimension)
        self._conn.execute(f"DELETE FROM {table} WHERE book_id = ?", (book_id,))
        self._conn.commit()

    def has_embeddings(self, book_id: str, provider_name: str, dimension: int) -> bool:
        table = _table_name(provider_name, dimension)
        cursor = self._conn.execute(
            f"SELECT 1 FROM {table} WHERE book_id = ? LIMIT 1", (book_id,)
        )
        return cursor.fetchone() is not None
