## Context

The CLI has 4 working commands (`ingest`, `embed`, `search`, `ask`) but lacks basic management commands — users can't list their books, delete them, or set their reading position. Each command also duplicates DB setup (~6 lines) and API-key validation (~4 lines), making the file long and inconsistent. Phase 7 adds the missing commands and cleans up the internals.

Most domain operations already exist: `BookRepository.get_all()`, `BookRepository.delete()`, `Book.set_current_page()`, `ChunkRepository.get_by_book()`. One small protocol addition is needed: `ChunkRepository.count_by_book()` for efficient chunk counting in `ListBooksUseCase`.

## Goals / Non-Goals

**Goals:**

- Add `books` command to list all books with key metadata
- Add `show <book-id>` command for detailed single-book view
- Add `delete <book-id>` command with confirmation
- Add `set-page <book-id> <page>` command for reading position
- Add `--verbose` global flag for debug output across all commands
- Extract shared DB/API-key setup into reusable helpers
- Consistent error formatting across all commands

**Non-Goals:**

- Interactive TUI or rich formatting (plain text is fine for v1)
- Config file support (env vars via direnv are sufficient)
- pydantic-settings integration (deferred — raw env vars work fine, no type-safety issue yet)
- New use cases for `ingest` or `embed` (those commands are complete)

## Decisions

### 1. Use cases for new commands

**Decision:** `ListBooksUseCase` in `app/list_books.py` returns `list[BookSummary]` where `BookSummary` is a frozen dataclass with `id`, `title`, `status`, `chunk_count`, `embedding_provider`, `current_page`. `DeleteBookUseCase` in `app/delete_book.py` handles cascading delete of book, chunks, and embeddings.

`DeleteBookUseCase` accepts `BookRepository` and `EmbeddingRepository` (not `ChunkRepository` — chunks cascade via SQL foreign key). It first fetches the book to read `embedding_provider` and `embedding_dimension`. If both are non-None, it calls `embedding_repo.delete_by_book(provider, dimension, book_id)` to clean up vec0 virtual table rows (which don't cascade). Then it calls `book_repo.delete(book_id)` which cascades to chunks automatically.

**Rationale:** Keeps CLI handlers thin — they only format output. The use cases handle validation and orchestration. `BookSummary` avoids exposing raw `Book` + separate chunk count query to the CLI layer. The delete use case doesn't need `ChunkRepository` because SQLite foreign keys handle chunk cleanup.

**Alternatives considered:**

- Query repos directly from CLI handlers: violates dependency direction (UI → App → Domain ← Infra)
- Reuse `Book` directly: doesn't include chunk_count, would need a second query in the CLI
- Pass `ChunkRepository` to `DeleteBookUseCase`: unnecessary — SQL ON DELETE CASCADE already handles chunks

### 2. BookSummary value object

**Decision:** Create `BookSummary` frozen dataclass in `domain/book_summary.py` with fields: `id: str`, `title: str`, `status: BookStatus`, `chunk_count: int`, `embedding_provider: str | None`, `current_page: int`.

**Rationale:** The `books` command needs chunk count alongside book metadata. Rather than returning `(Book, int)` tuples, a dedicated value object is cleaner and more extensible.

### 3. ChunkRepository.count_by_book protocol addition

**Decision:** Add `count_by_book(book_id: str) -> int` to the `ChunkRepository` protocol and implement it in `infra/storage/chunk_repo.py` as a simple `SELECT COUNT(*) FROM chunks WHERE book_id = ?`.

**Rationale:** `ListBooksUseCase` needs chunk counts per book for `BookSummary`. Using `len(get_by_book(book_id))` would load all chunk objects into memory just to count them. A dedicated count query is a single integer result — efficient and clean.

### 4. Shared DB helper

**Decision:** Extract a `_open_db(enable_vec: bool = False) -> Database` helper function in `main.py` that handles `DB_PATH.parent.mkdir()`, `Database()` construction, and `db.run_migrations(SCHEMA_DIR)`. Commands call this instead of repeating the 3 lines.

**Rationale:** Every command repeats the same 3 lines. A local helper in `main.py` eliminates this without introducing a new module. It stays private to the CLI layer.

### 5. Shared API-key validation

**Decision:** Extract `_require_env(name: str) -> str` helper in `main.py` that reads the env var and exits with a consistent error if missing.

**Rationale:** Four commands check API keys with slightly different patterns. A shared helper ensures consistent error messages and reduces boilerplate.

### 6. Global --verbose flag via typer callback

**Decision:** Add `--verbose` to the existing `@app.callback()`. Store the flag in a module-level variable (e.g., `_verbose: bool = False`). Commands check `_verbose` to print extra info.

**Rationale:** Typer's callback runs before any subcommand, making it the natural place for global options. Module-level state is simple and sufficient for a CLI (no concurrency concerns). Verbose output includes: model names, chunk counts, timing for API calls.

**Alternatives considered:**

- Pass verbose through typer Context: works but more complex plumbing
- Logging framework: overkill for a CLI with 6 commands

### 7. Delete with --yes flag

**Decision:** `delete` command asks for confirmation by default, skippable with `--yes` / `-y` flag. Uses `typer.confirm()`.

**Rationale:** Deleting a book cascades to chunks, embeddings, and chat history — this is destructive and irreversible. Confirmation prevents accidental data loss. `--yes` enables scripting.

## Risks / Trade-offs

**[Risk] Module-level verbose state** → Acceptable for a single-threaded CLI. Would need refactoring for a library API, but that's not planned.

**[Trade-off] BookSummary adds a new domain type** → Small cost for a clean API. Alternative (returning raw tuples) would be worse.

**[Trade-off] No pydantic-settings** → Deferred. Raw `os.environ.get()` works, the helper makes it consistent. pydantic-settings can be added when config complexity grows.
