# sqlite-storage

SQLite infrastructure — database connection, migration runner, and repository implementations. Located in `python/source/interactive_books/infra/storage/`.

## Requirements

### ST-1: Database connection manager

`Database` class in `infra/storage/database.py` manages a SQLite connection. Constructor accepts a database path (str or Path). Provides a `connection` property for raw access and a `close()` method.

### ST-2: WAL mode and foreign keys

Every new database connection enables WAL mode (`PRAGMA journal_mode=WAL`) and foreign keys (`PRAGMA foreign_keys=ON`). These are set immediately after connection, before any queries.

### ST-3: Migration runner reads from shared/schema/

`Database.run_migrations(schema_dir: Path)` reads all `*.sql` files from the given directory, filters to files matching the pattern `NNN_*.sql` (3+ digit prefix), and sorts by number.

### ST-4: Migration tracking table

The migration runner creates a `schema_migrations` table (if not exists) with columns: `version` (INTEGER PRIMARY KEY), `name` (TEXT), `applied_at` (TEXT). Each applied migration is recorded.

### ST-5: Idempotent migration application

The migration runner skips migrations already present in `schema_migrations`. Only unapplied migrations are executed, in ascending numerical order.

### ST-6: Migration failure handling

If a migration fails (SQL error), the runner raises `StorageError` with code `migration_failed` and includes the migration name and original error message. Partially applied migrations are rolled back (per-migration transaction).

### ST-7: SqliteBookRepository

`SqliteBookRepository` in `infra/storage/book_repo.py` implements the `BookRepository` protocol. Maps between Book domain objects and SQLite rows. Handles `save` (INSERT OR REPLACE), `get`, `get_all`, and `delete`.

### ST-8: SqliteChunkRepository

`SqliteChunkRepository` in `infra/storage/chunk_repo.py` implements the `ChunkRepository` protocol. Maps between Chunk domain objects and SQLite rows. `save_chunks` uses a transaction for bulk insert. `get_up_to_page` filters chunks where `start_page <= page`.

### ST-9: Cascade delete verification

Deleting a book via `SqliteBookRepository.delete()` cascades to all related chunks and chat messages (enforced by SQLite foreign keys with ON DELETE CASCADE, which requires `PRAGMA foreign_keys=ON`).

### ST-10: In-memory database for testing

`Database` accepts `":memory:"` as the path for in-memory databases, enabling fast isolated tests without filesystem I/O.
