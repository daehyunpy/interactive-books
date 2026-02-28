**Why:**
Phase B (Domain Layer) is complete — all Swift domain entities, value objects, protocols, and errors are implemented and tested. Before any use case, CLI command, or UI can function, data must persist across app launches. Every downstream phase (E through N) depends on storage: ingestion needs to save books and chunks, embeddings need to save vectors, chat needs to persist conversations and messages, and the CLI `books` command needs to list books from the database. This phase ports the Python SQLite storage layer to Swift, implementing all four relational repository protocols against the shared SQL schema. The EmbeddingRepository (sqlite-vec) is excluded — it's isolated in Phase D due to higher integration risk.

**What Changes:**
- Create `Infra/Storage/Database.swift` — SQLite connection manager using the system SQLite C API, with WAL mode, foreign keys enabled, and migration runner that reads from `shared/schema/`
- Create `Infra/Storage/BookRepository.swift` — implements the `BookRepository` protocol with SQL-backed CRUD (INSERT OR REPLACE, SELECT, DELETE with cascade)
- Create `Infra/Storage/ChunkRepository.swift` — implements the `ChunkRepository` protocol with batch insert, page-range queries, and count
- Create `Infra/Storage/ConversationRepository.swift` — implements the `ConversationRepository` protocol with CRUD ordered by `created_at DESC`
- Create `Infra/Storage/ChatMessageRepository.swift` — implements the `ChatMessageRepository` protocol with append-only save and chronological retrieval
- Create integration tests in `Tests/InteractiveBooksTests/Infra/Storage/` — against real in-memory SQLite databases verifying CRUD, cascade deletes, migration runner, and page-filtered queries
- Wire the `books` CLI command — `interactive-books books` lists all books from the database (first real command connected to storage)

**Capabilities:**

*New Capabilities:*
- `sqlite-connection` (Swift): Database connection manager with WAL mode, foreign keys, and shared schema migration runner
- `book-persistence` (Swift): SQL-backed BookRepository implementing the domain protocol
- `chunk-persistence` (Swift): SQL-backed ChunkRepository with batch insert and page-range filtering
- `conversation-persistence` (Swift): SQL-backed ConversationRepository with newest-first ordering
- `message-persistence` (Swift): SQL-backed ChatMessageRepository with chronological ordering
- `cli-books-command` (Swift): `interactive-books books` command listing all books from the database

*Modified Capabilities:*
- `Package.swift` — no new SPM dependencies needed; Swift uses the system SQLite C library directly via `import SQLite3`

**Impact:**
- **New files in `Sources/InteractiveBooksCore/Infra/Storage/`** (5 Swift files: Database, BookRepository, ChunkRepository, ConversationRepository, ChatMessageRepository)
- **New files in `Sources/CLI/`** (1 file: BooksCommand.swift or added to existing CLI entry point)
- **New test files in `Tests/InteractiveBooksTests/Infra/Storage/`** (~5 integration test files)
- **No external dependencies** — uses system SQLite3 C library (available on all Apple platforms)
- **No changes to domain layer** — implements existing protocols only
- **Reads shared schema from `shared/schema/`** — same migration files used by Python
