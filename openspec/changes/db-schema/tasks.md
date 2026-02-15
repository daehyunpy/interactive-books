## 1. SQL Schema (shared/schema/)

- [ ] 1.1 Create `shared/schema/001_initial.sql` with books table — id, title (non-empty CHECK), status (enum CHECK, default 'pending'), current_page (default 0), embedding_provider, embedding_dimension, created_at, updated_at
- [ ] 1.2 Add chunks table to 001_initial.sql — id, book_id (FK CASCADE), content, start_page (CHECK >= 1), end_page (CHECK >= start_page), chunk_index, created_at. Indexes on book_id and (book_id, start_page, end_page)
- [ ] 1.3 Add chat_messages table to 001_initial.sql — id, book_id (FK CASCADE), role (CHECK 'user'|'assistant'), content, created_at. Index on book_id

## 2. Domain Errors (domain/errors.py) — TDD

- [ ] 2.1 Write tests for DomainError base class, BookError with all codes, LLMError with all codes, StorageError with all codes (`tests/domain/test_errors.py`)
- [ ] 2.2 Implement `domain/errors.py` — DomainError base, BookErrorCode/LLMErrorCode/StorageErrorCode enums, BookError/LLMError/StorageError classes with code + message attributes

## 3. Domain Models (domain/) — TDD

- [ ] 3.1 Write tests for BookStatus enum values and string representation (`tests/domain/test_book.py`)
- [ ] 3.2 Write tests for Book creation (valid + invalid title), status transitions (valid + invalid), set_current_page, switch_embedding_provider (`tests/domain/test_book.py`)
- [ ] 3.3 Implement `domain/book.py` — BookStatus enum, Book dataclass with __post_init__ validation, transition methods, set_current_page, switch_embedding_provider
- [ ] 3.4 Write tests for Chunk creation (valid + invalid page ranges), immutability (`tests/domain/test_chunk.py`)
- [ ] 3.5 Implement `domain/chunk.py` — Chunk frozen dataclass with __post_init__ validation
- [ ] 3.6 Write tests for MessageRole enum and ChatMessage creation (`tests/domain/test_chat.py`)
- [ ] 3.7 Implement `domain/chat.py` — MessageRole enum, ChatMessage frozen dataclass

## 4. Repository Protocols (domain/protocols.py)

- [ ] 4.1 Define BookRepository protocol — save, get, get_all, delete methods using domain types
- [ ] 4.2 Define ChunkRepository protocol — save_chunks, get_by_book, get_up_to_page, delete_by_book methods using domain types
- [ ] 4.3 Verify no imports from infra/ or third-party packages

## 5. Database & Migration Runner (infra/storage/database.py) — TDD

- [ ] 5.1 Write tests for Database connection (WAL mode, foreign keys enabled), in-memory database support (`tests/infra/test_database.py`)
- [ ] 5.2 Write tests for migration runner — applies migrations in order, tracks in schema_migrations, skips already-applied, raises StorageError on failure (`tests/infra/test_database.py`)
- [ ] 5.3 Implement `infra/storage/__init__.py` and `infra/storage/database.py` — Database class with connection management, run_migrations method

## 6. Repository Implementations (infra/storage/) — TDD

- [ ] 6.1 Write tests for SqliteBookRepository — save, get, get_all, delete, update via save (`tests/infra/test_book_repo.py`)
- [ ] 6.2 Implement `infra/storage/book_repo.py` — SqliteBookRepository with domain ↔ row mapping
- [ ] 6.3 Write tests for SqliteChunkRepository — save_chunks, get_by_book (ordered by chunk_index), get_up_to_page (page filtering), delete_by_book (`tests/infra/test_chunk_repo.py`)
- [ ] 6.4 Implement `infra/storage/chunk_repo.py` — SqliteChunkRepository with domain ↔ row mapping
- [ ] 6.5 Write integration test for cascade delete — delete book, verify chunks and chat_messages also deleted (`tests/infra/test_cascade.py`)

## 7. Verification

- [ ] 7.1 Run `uv run pytest -x` — all tests pass
- [ ] 7.2 Run `uv run ruff check .` — no lint errors
- [ ] 7.3 Run `uv run pyright` — no type errors
- [ ] 7.4 Verify domain modules have zero imports from infra/ or third-party packages
