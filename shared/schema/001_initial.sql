-- 001_initial.sql
-- Initial schema: books, chunks, chat_messages

CREATE TABLE books (
    id                  TEXT PRIMARY KEY,
    title               TEXT NOT NULL CHECK (length(trim(title)) > 0),
    status              TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'ingesting', 'ready', 'failed')),
    current_page        INTEGER NOT NULL DEFAULT 0,
    embedding_provider  TEXT,
    embedding_dimension INTEGER,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE chunks (
    id          TEXT PRIMARY KEY,
    book_id     TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    start_page  INTEGER NOT NULL CHECK (start_page >= 1),
    end_page    INTEGER NOT NULL CHECK (end_page >= start_page),
    chunk_index INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_chunks_book_id ON chunks(book_id);
CREATE INDEX idx_chunks_book_page_range ON chunks(book_id, start_page, end_page);

CREATE TABLE chat_messages (
    id         TEXT PRIMARY KEY,
    book_id    TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_chat_messages_book_id ON chat_messages(book_id);
