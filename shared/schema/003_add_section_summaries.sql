CREATE TABLE IF NOT EXISTS section_summaries (
    id TEXT PRIMARY KEY NOT NULL,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(title) > 0),
    start_page INTEGER NOT NULL CHECK (start_page >= 1),
    end_page INTEGER NOT NULL CHECK (end_page >= start_page),
    summary TEXT NOT NULL CHECK (length(summary) > 0),
    key_statements TEXT NOT NULL DEFAULT '[]',
    section_index INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_section_summaries_book_id
    ON section_summaries(book_id);
