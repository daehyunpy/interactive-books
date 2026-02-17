# sql-schema

Delta spec for SQL schema changes to support agentic conversation. Adds `conversations` table, rewrites `chat_messages` foreign key from `book_id` to `conversation_id`, and adds `tool_result` to the role CHECK constraint.

## ADDED Requirements

### SS-8: Conversations table

The `conversations` table SHALL be added with columns:

- `id` (TEXT PRIMARY KEY)
- `book_id` (TEXT NOT NULL, FK to `books` ON DELETE CASCADE)
- `title` (TEXT NOT NULL)
- `created_at` (TEXT NOT NULL, default `datetime('now')`)

An index SHALL be created on `book_id` for efficient lookup of conversations by book.

#### Scenario: Conversations table exists

- **WHEN** the schema is applied
- **THEN** a `conversations` table exists with all specified columns and constraints

#### Scenario: Book foreign key enforced

- **WHEN** a conversation is inserted with a `book_id` that does not exist in `books`
- **THEN** the insert fails with a foreign key constraint violation

#### Scenario: Book deletion cascades to conversations

- **WHEN** a book is deleted from the `books` table
- **THEN** all conversations referencing that `book_id` are automatically deleted

#### Scenario: Index on book_id

- **WHEN** conversations are queried by `book_id`
- **THEN** an index on `conversations(book_id)` is used for efficient lookup

## MODIFIED Requirements

### SS-4: Chat messages table (MODIFIED)

The `chat_messages` table SHALL have columns:

- `id` (TEXT PRIMARY KEY)
- `conversation_id` (TEXT NOT NULL, FK to `conversations` ON DELETE CASCADE)
- `role` (TEXT NOT NULL, constrained to `'user'`|`'assistant'`|`'tool_result'`)
- `content` (TEXT NOT NULL)
- `created_at` (TEXT NOT NULL, default `datetime('now')`)

Index on `conversation_id`.

**Changes from original:**
- `book_id` column is REMOVED
- `conversation_id` column is ADDED with FK to `conversations` (not `books`)
- `role` CHECK constraint now includes `'tool_result'` in addition to `'user'` and `'assistant'`
- Index changed from `book_id` to `conversation_id`

#### Scenario: Chat messages table has conversation_id

- **WHEN** the schema is inspected
- **THEN** `chat_messages` has a `conversation_id` column and no `book_id` column

#### Scenario: Conversation foreign key enforced

- **WHEN** a chat message is inserted with a `conversation_id` that does not exist in `conversations`
- **THEN** the insert fails with a foreign key constraint violation

#### Scenario: Conversation deletion cascades to messages

- **WHEN** a conversation is deleted from the `conversations` table
- **THEN** all chat messages referencing that `conversation_id` are automatically deleted

#### Scenario: Book deletion cascades through conversations to messages

- **WHEN** a book is deleted from the `books` table
- **THEN** its conversations are deleted (via SS-8 cascade), and those conversations' messages are also deleted (via this cascade)

#### Scenario: tool_result role accepted

- **WHEN** a chat message is inserted with `role='tool_result'`
- **THEN** the insert succeeds

#### Scenario: Invalid role rejected

- **WHEN** a chat message is inserted with `role='system'`
- **THEN** the insert fails with a CHECK constraint violation

### SS-5: Column names match domain glossary (MODIFIED)

All column names SHALL match the "Domain Glossary" table in `docs/technical_design.md` -- "Cross-Platform Contracts". Column naming uses `snake_case`. This now includes the `conversations` table columns (`id`, `book_id`, `title`, `created_at`) and the updated `chat_messages` column (`conversation_id` replacing `book_id`).

#### Scenario: Glossary alignment for conversations

- **WHEN** the `conversations` table columns are compared to the domain glossary
- **THEN** all column names match: `id`, `book_id`, `title`, `created_at`

#### Scenario: Glossary alignment for chat_messages

- **WHEN** the `chat_messages` table columns are compared to the domain glossary
- **THEN** `conversation_id` matches the glossary entry for "Message conversation ref"

### SS-6: Cascade delete integrity (MODIFIED)

Deleting a row from `books` SHALL cascade to all related rows in `chunks`, `conversations`, and `chat_messages` (via conversations) through `ON DELETE CASCADE` foreign key constraints. Deleting a row from `conversations` SHALL cascade to all related rows in `chat_messages`.

#### Scenario: Full cascade chain

- **WHEN** a book is deleted that has chunks, conversations, and messages
- **THEN** all chunks are deleted (direct cascade), all conversations are deleted (direct cascade), and all messages are deleted (transitive cascade via conversations)

#### Scenario: Conversation-only cascade

- **WHEN** a conversation is deleted (but its book remains)
- **THEN** all messages for that conversation are deleted, but the book and other conversations are unaffected

## REMOVED Requirements

### SS-4 (original): Chat messages with book_id

**Reason:** `chat_messages.book_id` is replaced by `chat_messages.conversation_id`. Messages no longer reference books directly; they reference conversations, which reference books.

**Migration:** Since the `chat_messages` table and `ChatMessage` model are not yet in production use, the schema change can be folded into `001_initial.sql` or added as a new migration `003_add_conversations.sql` -- implementation decision.
