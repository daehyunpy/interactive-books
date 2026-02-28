**Context:**
Phase B is complete. The Swift package has `InteractiveBooksCore` (library) and `interactive-books` (CLI executable) targets. All domain entities (`Book`, `Chunk`, `Conversation`, `ChatMessage`), value objects, errors, and protocols (`BookRepository`, `ChunkRepository`, `ConversationRepository`, `ChatMessageRepository`, `EmbeddingRepository`) are defined. The Python storage layer is the reference implementation — it uses raw SQLite with WAL mode, foreign keys, a migration runner reading from `shared/schema/`, and INSERT OR REPLACE for upserts. The shared SQL schema (`001_initial.sql`, `002_add_embeddings.sql`, `003_add_section_summaries.sql`) defines the canonical table structures. The `EmbeddingRepository` is deferred to Phase D (sqlite-vec integration).

**Goals / Non-Goals:**

*Goals:*
- Implement a SQLite connection manager using the system SQLite3 C API
- Run shared SQL migrations from `shared/schema/` with idempotent tracking
- Implement `BookRepository`, `ChunkRepository`, `ConversationRepository`, `ChatMessageRepository` as SQL-backed adapters
- Write integration tests against real in-memory SQLite databases
- Wire the first CLI command (`books`) to display books from the database
- Match the Python storage layer's behavior for cross-platform schema fidelity

*Non-Goals:*
- No EmbeddingRepository implementation — deferred to Phase D (sqlite-vec)
- No sqlite-vec extension loading — Phase D
- No ORM or SwiftData — raw SQLite only
- No async repository methods — SQLite is synchronous local I/O
- No parser, chunker, or embedding implementations — those are Phases E–G
- No CLI commands beyond `books` — `ingest`, `embed`, `search`, `delete` come in later phases

**Decisions:**

### 1. System SQLite3 C API via `import SQLite3`

**Decision:** Use the system SQLite3 C library directly via `import SQLite3` (the Darwin/Glibc module). No third-party SQLite wrapper libraries.

**Rationale:** The system SQLite3 library is available on every Apple platform (iOS, macOS, visionOS). It matches Python's approach of using the standard library `sqlite3` module. A thin Swift wrapper class (`Database`) provides ergonomic access while keeping full control over SQL execution, pragma settings, and migration behavior. Third-party wrappers (GRDB, SQLite.swift) add abstraction that fights the shared schema requirement.

**Alternative:** GRDB or SQLite.swift. These add query builder DSLs that obscure the raw SQL, making it harder to verify schema fidelity with the shared `.sql` files. They also add SPM dependencies unnecessarily.

### 2. Thin Database wrapper with prepare/bind/step pattern

**Decision:** `Database` class wraps an `OpaquePointer` (sqlite3*) and provides helper methods: `execute(sql:)` for DDL/DML without results, `query(sql:bind:)` for SELECT returning rows, and `run(sql:bind:)` for parameterized INSERT/UPDATE/DELETE. Prepared statements use `sqlite3_prepare_v2`, bind parameters positionally, step through results, and finalize.

**Rationale:** The C API requires careful lifecycle management of statement pointers. Centralizing prepare/bind/step/finalize in the `Database` class prevents resource leaks and provides a single place for error handling. The helper methods match common usage patterns: DDL execution, parameterized queries, and parameterized mutations.

**Note:** Statement parameters use `?` placeholders (positional binding), matching the Python `sqlite3` convention.

### 3. Migration runner with schema_migrations tracking

**Decision:** Port the Python migration runner pattern exactly. The `Database.runMigrations(schemaDir:)` method:
1. Creates `schema_migrations` table if not exists
2. Reads `.sql` files matching `^\d{3,}_.+\.sql$` from the given directory
3. Sorts by numeric prefix
4. Skips already-applied versions
5. Applies each unapplied migration in a transaction
6. Records the version, name, and timestamp in `schema_migrations`
7. Throws `StorageError.migrationFailed` on failure

**Rationale:** Exact behavioral match with Python ensures both codebases can read/write the same database file. The shared schema directory is the single source of truth.

### 4. Row-to-entity mapping via static factory methods

**Decision:** Each repository has a private static `fromRow(_:)` method that maps a SQLite row (array of column values) to the domain entity. Entity construction uses the same initializers defined in Phase B.

**Rationale:** Centralizes the mapping logic per repository. Matches the Python `_row_to_book()`, `_row_to_chunk()`, etc. pattern. Keeps the mapping close to the SQL queries so column order mismatches are caught early.

**Row mapping specifics:**
- Timestamps: stored as ISO 8601 strings, parsed with `ISO8601DateFormatter`
- Enums: stored as raw string values (`"pending"`, `"user"`, etc.), constructed via `rawValue` initializer
- Nullable columns: `embedding_provider`, `embedding_dimension` on Book — handle `NULL` → `nil`
- Book initialization: uses a direct property-setting init (bypassing validation) for hydration from DB, since data was validated on save

### 5. INSERT OR REPLACE for Book and Conversation upserts

**Decision:** `BookRepository.save()` and `ConversationRepository.save()` use `INSERT OR REPLACE` (equivalent to `INSERT ... ON CONFLICT(id) DO UPDATE SET ...`). `ChunkRepository.saveChunks()` uses plain `INSERT` (chunks are immutable). `ChatMessageRepository.save()` uses plain `INSERT` (messages are append-only).

**Rationale:** Matches the Python implementation exactly. Books and Conversations can be updated (status changes, renames); chunks and messages are write-once.

### 6. In-memory SQLite for tests

**Decision:** Integration tests use `Database(path: ":memory:")` for fast, isolated testing. Each test creates a fresh database, runs migrations, and exercises the repository.

**Rationale:** Matches the Python test approach (`Database(":memory:")`). No filesystem cleanup needed. Tests run fast and in parallel.

### 7. Database path resolution for CLI

**Decision:** The CLI resolves the database path as `<project_root>/data/books.db`, matching the Python convention. The `data/` directory is created if it doesn't exist. The schema directory is resolved as `<project_root>/shared/schema/`.

**Rationale:** Cross-platform compatibility — the same `books.db` file can be read by both Python and Swift CLIs, enabling interop testing.

**Note:** The Swift app (Phase J+) will use a platform-specific path (e.g., Application Support). This decision is for the CLI only.

### 8. Sendable conformance for repositories

**Decision:** All repository classes conform to `Sendable` (required by the domain protocols). Since `OpaquePointer` (sqlite3*) is not `Sendable`, repository classes use `@unchecked Sendable`. Thread safety is the caller's responsibility — the CLI is single-threaded; the app layer (Phase I+) will serialize access.

**Rationale:** The domain protocols require `Sendable` conformance (established in Phase B). SQLite connections are not thread-safe by default. The caller (use case layer) is responsible for serializing access, matching the Python pattern where the CLI runs single-threaded.

### 9. `books` CLI command wiring

**Decision:** Add a `BooksCommand` struct conforming to `ParsableCommand` in `Sources/CLI/`. It creates a `Database`, runs migrations, instantiates `BookRepository`, calls `getAll()`, and prints a formatted table of books (title, status, chunk count). Chunk count requires `ChunkRepository.countByBook()`.

**Rationale:** The app build plan specifies `interactive-books books` as the first CLI command wired to storage (Phase C acceptance criteria). This validates the full stack: CLI → repository → SQLite → shared schema.

**Risks / Trade-offs:**

- **[Risk] SQLite3 C API is verbose and error-prone** → Mitigated by the thin `Database` wrapper that encapsulates prepare/bind/step/finalize. All SQLite errors are checked and converted to `StorageError`.

- **[Risk] System SQLite version varies by OS** → All features used (WAL, foreign keys, `INSERT OR REPLACE`) are available since SQLite 3.7+ (iOS 5 era). No version concerns for iOS 26+.

- **[Trade-off] `@unchecked Sendable` on repositories** → Acceptable: same rationale as Phase B aggregate roots. Thread safety is the application layer's responsibility. Single-threaded CLI doesn't need synchronization.

- **[Trade-off] No connection pooling** → Not needed for CLI (single connection). The app (Phase I+) will need to consider this, but it's out of scope for Phase C.

- **[Trade-off] Book hydration bypasses validation** → When loading from DB, we trust the data was validated on save. Using a separate internal init avoids re-validating known-good data and avoids `throws` on read paths. This is clearly documented and matches the Python approach where `_row_to_book()` constructs directly.
