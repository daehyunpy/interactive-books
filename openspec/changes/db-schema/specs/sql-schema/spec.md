# sql-schema

Shared SQL migration defining the initial database tables for books, chunks, and chat messages.

## Requirements

### SS-1: Migration file location and naming

`shared/schema/001_initial.sql` exists and follows the numbered migration naming convention (`NNN_name.sql`). The file contains plain SQL — no ORM-specific syntax, no Python or Swift code.

### SS-2: Books table

The `books` table has columns: `id` (TEXT PRIMARY KEY), `title` (TEXT NOT NULL, non-empty), `status` (TEXT NOT NULL, constrained to 'pending'|'ingesting'|'ready'|'failed', default 'pending'), `current_page` (INTEGER NOT NULL, default 0), `embedding_provider` (TEXT, nullable), `embedding_dimension` (INTEGER, nullable), `created_at` (TEXT NOT NULL, default datetime('now')), `updated_at` (TEXT NOT NULL, default datetime('now')).

### SS-3: Chunks table

The `chunks` table has columns: `id` (TEXT PRIMARY KEY), `book_id` (TEXT NOT NULL, FK to books ON DELETE CASCADE), `content` (TEXT NOT NULL), `start_page` (INTEGER NOT NULL, CHECK >= 1), `end_page` (INTEGER NOT NULL, CHECK >= start_page), `chunk_index` (INTEGER NOT NULL), `created_at` (TEXT NOT NULL, default datetime('now')). Indexes on `book_id` and `(book_id, start_page, end_page)`.

### SS-4: Chat messages table

The `chat_messages` table has columns: `id` (TEXT PRIMARY KEY), `book_id` (TEXT NOT NULL, FK to books ON DELETE CASCADE), `role` (TEXT NOT NULL, constrained to 'user'|'assistant'), `content` (TEXT NOT NULL), `created_at` (TEXT NOT NULL, default datetime('now')). Index on `book_id`.

### SS-5: Column names match domain glossary

All column names match the "Domain Glossary" table in `docs/technical_design.md` → "Cross-Platform Contracts". Column naming uses `snake_case`.

### SS-6: Cascade delete integrity

Deleting a row from `books` cascades to all related rows in `chunks` and `chat_messages` via `ON DELETE CASCADE` foreign key constraints.
