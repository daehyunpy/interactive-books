import json
import sqlite3
from datetime import datetime, timezone

from interactive_books.domain.protocols import SummaryRepository as SummaryRepositoryPort
from interactive_books.domain.section_summary import KeyStatement, SectionSummary
from interactive_books.infra.storage.database import Database

_COLUMNS = "id, book_id, title, start_page, end_page, summary, key_statements, section_index, created_at"


class SummaryRepository(SummaryRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection

    def save_all(self, book_id: str, summaries: list[SectionSummary]) -> None:
        self._conn.execute(
            "DELETE FROM section_summaries WHERE book_id = ?", (book_id,)
        )
        self._conn.executemany(
            f"""
            INSERT INTO section_summaries ({_COLUMNS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    s.id,
                    s.book_id,
                    s.title,
                    s.start_page,
                    s.end_page,
                    s.summary,
                    json.dumps(
                        [
                            {"statement": ks.statement, "page": ks.page}
                            for ks in s.key_statements
                        ]
                    ),
                    s.section_index,
                    s.created_at.isoformat(),
                )
                for s in summaries
            ],
        )
        self._conn.commit()

    def get_by_book(self, book_id: str) -> list[SectionSummary]:
        cursor = self._conn.execute(
            f"SELECT {_COLUMNS} FROM section_summaries WHERE book_id = ? ORDER BY section_index",
            (book_id,),
        )
        return [self._row_to_summary(row) for row in cursor.fetchall()]

    def delete_by_book(self, book_id: str) -> None:
        self._conn.execute(
            "DELETE FROM section_summaries WHERE book_id = ?", (book_id,)
        )
        self._conn.commit()

    @staticmethod
    def _row_to_summary(row: sqlite3.Row | tuple) -> SectionSummary:  # type: ignore[type-arg]
        raw_statements = json.loads(row[6])
        key_statements = [
            KeyStatement(statement=ks["statement"], page=ks["page"])
            for ks in raw_statements
        ]
        return SectionSummary(
            id=row[0],
            book_id=row[1],
            title=row[2],
            start_page=row[3],
            end_page=row[4],
            summary=row[5],
            key_statements=key_statements,
            section_index=row[7],
            created_at=datetime.fromisoformat(row[8]).replace(tzinfo=timezone.utc),
        )
