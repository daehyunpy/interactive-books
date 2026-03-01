import Foundation
@testable import InteractiveBooksCore

enum StorageTestHelper {
    static func createTestDatabase() throws -> Database {
        let db = try Database(path: ":memory:")
        try createBooksTable(db)
        try createChunksTable(db)
        try createConversationsTable(db)
        try createChatMessagesTable(db)
        try createSectionSummariesTable(db)
        return db
    }

    private static func createBooksTable(_ db: Database) throws {
        try db.execute(sql: """
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
        )
        """)
    }

    private static func createChunksTable(_ db: Database) throws {
        try db.execute(sql: """
        CREATE TABLE chunks (
            id          TEXT PRIMARY KEY,
            book_id     TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            content     TEXT NOT NULL,
            start_page  INTEGER NOT NULL CHECK (start_page >= 1),
            end_page    INTEGER NOT NULL CHECK (end_page >= start_page),
            chunk_index INTEGER NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        try db.execute(sql: "CREATE INDEX idx_chunks_book_id ON chunks(book_id)")
        try db.execute(sql: "CREATE INDEX idx_chunks_book_page_range ON chunks(book_id, start_page, end_page)")
    }

    private static func createConversationsTable(_ db: Database) throws {
        try db.execute(sql: """
        CREATE TABLE conversations (
            id         TEXT PRIMARY KEY,
            book_id    TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            title      TEXT NOT NULL CHECK (length(trim(title)) > 0),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        try db.execute(sql: "CREATE INDEX idx_conversations_book_id ON conversations(book_id)")
    }

    private static func createChatMessagesTable(_ db: Database) throws {
        try db.execute(sql: """
        CREATE TABLE chat_messages (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool_result')),
            content         TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        try db.execute(sql: "CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id)")
    }

    private static func createSectionSummariesTable(_ db: Database) throws {
        try db.execute(sql: """
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
        )
        """)
        try db.execute(sql: "CREATE INDEX IF NOT EXISTS idx_section_summaries_book_id ON section_summaries(book_id)")
    }

    nonisolated(unsafe) static let iso8601Formatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    // swiftlint:disable:next force_unwrapping
    static let fixedDate: Date = iso8601Formatter.date(from: "2025-01-15T10:30:00Z")!

    // swiftlint:disable:next force_unwrapping
    static let fixedDate2: Date = iso8601Formatter.date(from: "2025-01-16T12:00:00Z")!

    // swiftlint:disable:next force_unwrapping
    static let fixedDate3: Date = iso8601Formatter.date(from: "2025-01-17T08:00:00Z")!
}
