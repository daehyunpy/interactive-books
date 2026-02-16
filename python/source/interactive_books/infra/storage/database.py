import re
import sqlite3
from pathlib import Path

import sqlite_vec
from interactive_books.domain.errors import StorageError, StorageErrorCode

MIGRATION_PATTERN = re.compile(r"^(\d{3,})_.+\.sql$")


class Database:
    def __init__(self, path: str | Path, *, enable_vec: bool = False) -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        if enable_vec:
            self._connection.enable_load_extension(True)
            sqlite_vec.load(self._connection)
            self._connection.enable_load_extension(False)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()

    def run_migrations(self, schema_dir: Path) -> None:
        self._ensure_migration_table()
        applied = self._get_applied_versions()

        for path, version in self._sorted_migration_files(schema_dir):
            if version not in applied:
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

    def _sorted_migration_files(self, schema_dir: Path) -> list[tuple[Path, int]]:
        results = []
        for path in sorted(schema_dir.iterdir()):
            match = MIGRATION_PATTERN.match(path.name) if path.is_file() else None
            if match:
                results.append((path, int(match.group(1))))
        return results

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
