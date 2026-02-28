import Foundation

public final class SQLiteConversationRepository: ConversationRepository, @unchecked Sendable {
    private let database: Database

    private static let selectColumns =
        "id, book_id, title, created_at"

    public init(database: Database) {
        self.database = database
    }

    public func save(_ conversation: Conversation) throws {
        try database.run(
            sql: """
            INSERT OR REPLACE INTO conversations (\(Self.selectColumns))
            VALUES (?, ?, ?, ?)
            """,
            bind: [
                .text(conversation.id),
                .text(conversation.bookId),
                .text(conversation.title),
                .text(DateFormatting.iso8601String(from: conversation.createdAt)),
            ],
        )
    }

    public func get(_ conversationId: String) throws -> Conversation? {
        let rows = try database.query(
            sql: "SELECT \(Self.selectColumns) FROM conversations WHERE id = ?",
            bind: [.text(conversationId)],
        )
        guard let row = rows.first else { return nil }
        return try fromRow(row)
    }

    public func getByBook(_ bookId: String) throws -> [Conversation] {
        let rows = try database.query(
            sql: "SELECT \(Self.selectColumns) FROM conversations WHERE book_id = ? ORDER BY created_at DESC",
            bind: [.text(bookId)],
        )
        return try rows.map { try fromRow($0) }
    }

    public func delete(_ conversationId: String) throws {
        try database.run(
            sql: "DELETE FROM conversations WHERE id = ?",
            bind: [.text(conversationId)],
        )
    }

    private func fromRow(_ row: [SQLiteValue]) throws -> Conversation {
        guard case let .text(id) = row[0],
              case let .text(bookId) = row[1],
              case let .text(title) = row[2],
              case let .text(createdAtStr) = row[3],
              let createdAt = DateFormatting.date(from: createdAtStr)
        else {
            throw StorageError.dbCorrupted("Invalid conversation row data")
        }

        return Conversation(
            fromRow: id,
            bookId: bookId,
            title: title,
            createdAt: createdAt,
        )
    }
}
