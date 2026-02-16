import re
import sqlite3
from pathlib import Path

from interactive_books.domain.errors import StorageError, StorageErrorCode

MIGRATION_PATTERN = re.compile(r"^(\d{3,})_.+\.sql$")


class Database:
    def __init__(self, path: str) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()

    def run_migrations(self, schema_dir: Path) -> None:
        self._ensure_migration_table()
        applied = self._get_applied_versions()

        for path in self._sorted_migration_files(schema_dir):
            match = MIGRATION_PATTERN.match(path.name)
            if not match:
                continue
            version = int(match.group(1))
            if version in applied:
                continue
            self._apply_migration(path, version)

    def _ensure_migration_table(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER PRIMARY KEY,
                name       TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._connection.commit()

    def _get_applied_versions(self) -> set[int]:
        cursor = self._connection.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}

    def _sorted_migration_files(self, schema_dir: Path) -> list[Path]:
        files = [
            f for f in sorted(schema_dir.iterdir())
            if f.is_file() and MIGRATION_PATTERN.match(f.name)
        ]
        return files

    def _apply_migration(self, path: Path, version: int) -> None:
        sql = path.read_text()
        try:
            self._connection.executescript(sql)
            self._connection.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (version, path.name),
            )
            self._connection.commit()
        except sqlite3.Error as e:
            self._connection.rollback()
            raise StorageError(
                StorageErrorCode.MIGRATION_FAILED,
                f"Migration '{path.name}' failed: {e}",
            ) from e
