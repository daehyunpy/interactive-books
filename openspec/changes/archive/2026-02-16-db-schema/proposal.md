## Why

Phase 2 of the 8-phase build order. Phase 1 (scaffold) is complete — the monorepo structure, package configuration, environment setup, and CI pipeline exist. Before any feature logic (ingestion, embeddings, retrieval, Q&A) can begin, the data layer must exist: SQLite schema, domain models enforcing cross-platform invariants, error types, and storage adapters. Every subsequent phase depends on this foundation.

## What Changes

- Create `shared/schema/001_initial.sql` — books, chunks, chat_messages tables with constraints and indexes
- Create `python/source/interactive_books/domain/book.py` — Book aggregate root with BookStatus enum, status transitions, invariant enforcement
- Create `python/source/interactive_books/domain/chunk.py` — Chunk value object (immutable)
- Create `python/source/interactive_books/domain/chat.py` — ChatMessage entity with MessageRole enum
- Create `python/source/interactive_books/domain/errors.py` — BookError, LLMError, StorageError typed exceptions
- Create `python/source/interactive_books/domain/protocols.py` — BookRepository, ChunkRepository protocols
- Create `python/source/interactive_books/infra/storage/database.py` — SQLite connection manager + migration runner
- Create `python/source/interactive_books/infra/storage/book_repo.py` — SQLite BookRepository implementation
- Create `python/source/interactive_books/infra/storage/chunk_repo.py` — SQLite ChunkRepository implementation
- Create tests mirroring each module in `python/tests/domain/` and `python/tests/infra/`

## Capabilities

### New Capabilities

- `sql-schema`: Shared SQL migration file (001_initial.sql) defining books, chunks, and chat_messages tables with all cross-platform constraints
- `domain-models`: Domain entities enforcing invariants — Book aggregate root (status transitions, page validation), Chunk value object (page range validation), ChatMessage entity, BookStatus and MessageRole enums
- `domain-errors`: Typed domain exceptions — BookError, LLMError, StorageError with enumerated error cases matching the cross-platform error taxonomy
- `repository-protocols`: Storage abstractions in the domain layer — BookRepository and ChunkRepository protocols using only domain types
- `sqlite-storage`: SQLite infrastructure — database connection (WAL mode, foreign keys), migration runner (tracks applied migrations), BookRepository and ChunkRepository implementations

### Modified Capabilities

None — Phase 1 created structure only, no logic to modify.

## Impact

- **New files in `shared/schema/`** — cross-platform contract (SQL migration source of truth)
- **New domain modules** in `python/source/interactive_books/domain/` (5 files)
- **New infrastructure modules** in `python/source/interactive_books/infra/storage/` (3 files)
- **New test files** in `python/tests/domain/` and `python/tests/infra/` (~8 files)
- **No new external dependencies** — sqlite3 is Python stdlib
- **No changes to existing Phase 1 files** (except adding `infra/storage/__init__.py`)
