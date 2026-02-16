from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from interactive_books.domain.errors import StorageError, StorageErrorCode
from interactive_books.infra.storage.database import Database


class TestDatabaseConnection:
    def test_in_memory_database(self) -> None:
        db = Database(":memory:")
        assert db.connection is not None
        db.close()

    def test_wal_mode_enabled_on_file_database(self) -> None:
        with TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))
            cursor = db.connection.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            assert mode == "wal"
            db.close()

    def test_foreign_keys_enabled(self) -> None:
        db = Database(":memory:")
        cursor = db.connection.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]
        assert enabled == 1
        db.close()

    def test_file_based_database(self) -> None:
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            assert db_path.exists()
            db.close()


class TestMigrationRunner:
    def test_applies_single_migration(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_initial.sql").write_text(
                "CREATE TABLE test (id TEXT PRIMARY KEY);"
            )

            db = Database(":memory:")
            db.run_migrations(schema_dir)

            cursor = db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
            )
            assert cursor.fetchone() is not None
            db.close()

    def test_applies_migrations_in_order(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_first.sql").write_text(
                "CREATE TABLE first (id TEXT PRIMARY KEY);"
            )
            (schema_dir / "002_second.sql").write_text(
                "CREATE TABLE second (id TEXT PRIMARY KEY, first_id TEXT REFERENCES first(id));"
            )

            db = Database(":memory:")
            db.run_migrations(schema_dir)

            cursor = db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('first', 'second') ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert tables == ["first", "second"]
            db.close()

    def test_tracks_applied_migrations(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_initial.sql").write_text(
                "CREATE TABLE test (id TEXT PRIMARY KEY);"
            )

            db = Database(":memory:")
            db.run_migrations(schema_dir)

            cursor = db.connection.execute(
                "SELECT version, name FROM schema_migrations"
            )
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "001_initial.sql"
            db.close()

    def test_skips_already_applied_migrations(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_initial.sql").write_text(
                "CREATE TABLE test (id TEXT PRIMARY KEY);"
            )

            db = Database(":memory:")
            db.run_migrations(schema_dir)
            # Run again — should not raise (table already exists would fail if re-applied)
            db.run_migrations(schema_dir)

            cursor = db.connection.execute("SELECT COUNT(*) FROM schema_migrations")
            assert cursor.fetchone()[0] == 1
            db.close()

    def test_raises_storage_error_on_bad_sql(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_bad.sql").write_text("THIS IS NOT SQL;")

            db = Database(":memory:")
            with pytest.raises(StorageError) as exc_info:
                db.run_migrations(schema_dir)
            assert exc_info.value.code == StorageErrorCode.MIGRATION_FAILED
            db.close()

    def test_ignores_non_matching_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "001_initial.sql").write_text(
                "CREATE TABLE test (id TEXT PRIMARY KEY);"
            )
            (schema_dir / "README.md").write_text("Not a migration")
            (schema_dir / ".gitkeep").write_text("")

            db = Database(":memory:")
            db.run_migrations(schema_dir)

            cursor = db.connection.execute("SELECT COUNT(*) FROM schema_migrations")
            assert cursor.fetchone()[0] == 1
            db.close()
