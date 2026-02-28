## 1. Database Connection Manager

- [ ] 1.1 Write tests for `Database` initialization — creates a connection, WAL mode is enabled (`PRAGMA journal_mode` returns `"wal"`), foreign keys are enabled (`PRAGMA foreign_keys` returns `1`) (`tests/Infra/Storage/DatabaseTests.swift`)
- [ ] 1.2 Write tests for `Database` migration runner — applies migrations from a directory in numeric order, skips already-applied migrations, records applied versions in `schema_migrations` table (`tests/Infra/Storage/DatabaseTests.swift`)
- [ ] 1.3 Write test for migration failure — invalid SQL in a migration file throws `StorageError.migrationFailed` with migration name in the message (`tests/Infra/Storage/DatabaseTests.swift`)
- [ ] 1.4 Write test for migration file pattern matching — only files matching `^\d{3,}_.+\.sql$` are picked up; non-matching files (`.DS_Store`, `README.md`, `1_too_short.sql`) are ignored (`tests/Infra/Storage/DatabaseTests.swift`)
- [ ] 1.5 Implement `Infra/Storage/Database.swift` — thin wrapper around SQLite3 C API (`OpaquePointer`):
  - `init(path: String)` — opens connection, sets WAL mode and foreign keys
  - `close()` — closes connection
  - `execute(sql:)` — runs DDL/DML without results
  - `query(sql:bind:)` — runs SELECT with positional `?` bindings, returns `[[SQLiteValue]]` where `SQLiteValue` is an enum (`text(String)`, `integer(Int)`, `real(Double)`, `null`)
  - `run(sql:bind:)` — runs parameterized INSERT/UPDATE/DELETE
  - `runMigrations(schemaDir:)` — reads `.sql` files from directory, filters by pattern `^\d{3,}_.+\.sql$`, sorts by numeric prefix, creates `schema_migrations` table if needed, applies unapplied migrations, records each in `schema_migrations`, throws `StorageError.migrationFailed` on failure

## 2. BookRepository

- [ ] 2.1 Write tests for `BookRepository.save()` — saves a book and retrieves it with matching fields (id, title, status, currentPage, embeddingProvider, embeddingDimension, createdAt, updatedAt) (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.2 Write test for `BookRepository.save()` upsert — saving a book with the same ID updates its fields (title, status, currentPage) (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.3 Write test for `BookRepository.get()` — returns nil for non-existent book ID (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.4 Write test for `BookRepository.getAll()` — returns all saved books (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.5 Write test for `BookRepository.delete()` — deletes a book and verifies `get()` returns nil (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.6 Write test for cascade delete — deleting a book also deletes its chunks, conversations, and messages (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.7 Write test for nullable fields — saves a book with nil `embeddingProvider` and `embeddingDimension`, retrieves it with nil values (`tests/Infra/Storage/BookRepositoryTests.swift`)
- [ ] 2.8 Implement `Infra/Storage/BookRepository.swift` — implements `BookRepository` protocol:
  - `save(_:)` — INSERT OR REPLACE with all 8 columns, timestamps as ISO 8601 strings, status as raw value
  - `get(_:)` — SELECT by id, `fromRow()` maps to `Book` entity, returns nil if not found
  - `getAll()` — SELECT all, maps each row to `Book`
  - `delete(_:)` — DELETE by id (cascade handles related data)
  - Private `fromRow(_:)` — maps column values to `Book` init (handles ISO 8601 date parsing, `BookStatus` raw value, nullable embedding fields)

## 3. ChunkRepository

- [ ] 3.1 Write tests for `ChunkRepository.saveChunks()` and `getByBook()` — saves multiple chunks, retrieves them ordered by chunk_index (`tests/Infra/Storage/ChunkRepositoryTests.swift`)
- [ ] 3.2 Write test for `ChunkRepository.getUpToPage()` — saves chunks with varying page ranges, queries with a page limit, returns only chunks where `start_page <= page` ordered by chunk_index (`tests/Infra/Storage/ChunkRepositoryTests.swift`)
- [ ] 3.3 Write test for `ChunkRepository.countByBook()` — returns correct count, returns 0 for book with no chunks (`tests/Infra/Storage/ChunkRepositoryTests.swift`)
- [ ] 3.4 Write test for `ChunkRepository.deleteByBook()` — deletes all chunks for a book, chunks for other books are unaffected (`tests/Infra/Storage/ChunkRepositoryTests.swift`)
- [ ] 3.5 Implement `Infra/Storage/ChunkRepository.swift` — implements `ChunkRepository` protocol:
  - `saveChunks(bookId:chunks:)` — batch INSERT in a transaction (loop over chunks with prepared statement)
  - `getByBook(_:)` — SELECT by book_id ORDER BY chunk_index
  - `getUpToPage(bookId:page:)` — SELECT WHERE book_id = ? AND start_page <= ? ORDER BY chunk_index
  - `countByBook(_:)` — SELECT COUNT(*) WHERE book_id = ?
  - `deleteByBook(_:)` — DELETE WHERE book_id = ?
  - Private `fromRow(_:)` — maps to `Chunk` init (throwing, handles date parsing)

## 4. ConversationRepository

- [ ] 4.1 Write tests for `ConversationRepository.save()` and `get()` — saves a conversation, retrieves it with matching fields (id, bookId, title, createdAt) (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.2 Write test for `ConversationRepository.save()` upsert — saving a conversation with the same ID updates the title (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.3 Write test for `ConversationRepository.get()` — returns nil for non-existent ID (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.4 Write test for `ConversationRepository.getByBook()` — returns conversations ordered by `created_at` DESC (most recent first) (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.5 Write test for `ConversationRepository.getByBook()` — returns empty list for book with no conversations (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.6 Write test for `ConversationRepository.delete()` — deletes the conversation, cascades to its messages (`tests/Infra/Storage/ConversationRepositoryTests.swift`)
- [ ] 4.7 Implement `Infra/Storage/ConversationRepository.swift` — implements `ConversationRepository` protocol:
  - `save(_:)` — INSERT OR REPLACE with 4 columns
  - `get(_:)` — SELECT by id, returns nil if not found
  - `getByBook(_:)` — SELECT by book_id ORDER BY created_at DESC
  - `delete(_:)` — DELETE by id (cascade handles messages)
  - Private `fromRow(_:)` — maps to `Conversation` init (throwing, handles date parsing)

## 5. ChatMessageRepository

- [ ] 5.1 Write tests for `ChatMessageRepository.save()` and `getByConversation()` — saves multiple messages with different roles (user, assistant, tool_result), retrieves them in chronological order (`created_at ASC`) (`tests/Infra/Storage/ChatMessageRepositoryTests.swift`)
- [ ] 5.2 Write test for `ChatMessageRepository.getByConversation()` — returns empty list for conversation with no messages (`tests/Infra/Storage/ChatMessageRepositoryTests.swift`)
- [ ] 5.3 Write test for `ChatMessageRepository.deleteByConversation()` — deletes all messages for a conversation, messages for other conversations are unaffected (`tests/Infra/Storage/ChatMessageRepositoryTests.swift`)
- [ ] 5.4 Implement `Infra/Storage/ChatMessageRepository.swift` — implements `ChatMessageRepository` protocol:
  - `save(_:)` — INSERT with 5 columns (append-only, no upsert)
  - `getByConversation(_:)` — SELECT by conversation_id ORDER BY created_at ASC
  - `deleteByConversation(_:)` — DELETE WHERE conversation_id = ?
  - Private `fromRow(_:)` — maps to `ChatMessage` init (handles date parsing, `MessageRole` raw value)

## 6. CLI `books` Command

- [ ] 6.1 Implement `Sources/CLI/BooksCommand.swift` — `ParsableCommand` that opens the database (path: `<project_root>/data/books.db`), runs migrations (schema dir: `<project_root>/shared/schema/`), instantiates `BookRepository` and `ChunkRepository`, calls `getAll()`, prints a formatted table with columns: Title, Status, Chunks, Current Page. Shows "No books found." if empty.
- [ ] 6.2 Register `BooksCommand` in `InteractiveBooksCLI.subcommands` in `Sources/CLI/InteractiveBooks.swift`

## 7. Verification

- [ ] 7.1 Verify all Infra/Storage files import only from `InteractiveBooksCore/Domain/` and system frameworks (Foundation, SQLite3) — no imports from App/ or UI/
- [ ] 7.2 Verify `swift build` succeeds
- [ ] 7.3 Verify `swift test` passes — all integration tests green
- [ ] 7.4 Verify shared schema migrations (`shared/schema/001_initial.sql`, `002_add_embeddings.sql`, `003_add_section_summaries.sql`) are applied correctly by the migration runner
