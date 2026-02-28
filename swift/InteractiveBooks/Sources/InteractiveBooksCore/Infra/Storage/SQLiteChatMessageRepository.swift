import Foundation

public final class SQLiteChatMessageRepository: ChatMessageRepository, @unchecked Sendable {
    private let database: Database

    private static let selectColumns =
        "id, conversation_id, role, content, created_at"

    public init(database: Database) {
        self.database = database
    }

    public func save(_ message: ChatMessage) throws {
        try database.run(
            sql: """
                INSERT INTO chat_messages (\(Self.selectColumns))
                VALUES (?, ?, ?, ?, ?)
                """,
            bind: [
                .text(message.id),
                .text(message.conversationId),
                .text(message.role.rawValue),
                .text(message.content),
                .text(DateFormatting.iso8601String(from: message.createdAt)),
            ]
        )
    }

    public func getByConversation(_ conversationId: String) throws -> [ChatMessage] {
        let rows = try database.query(
            sql: "SELECT \(Self.selectColumns) FROM chat_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            bind: [.text(conversationId)]
        )
        return try rows.map { try fromRow($0) }
    }

    public func deleteByConversation(_ conversationId: String) throws {
        try database.run(
            sql: "DELETE FROM chat_messages WHERE conversation_id = ?",
            bind: [.text(conversationId)]
        )
    }

    private func fromRow(_ row: [SQLiteValue]) throws -> ChatMessage {
        guard case let .text(id) = row[0],
              case let .text(conversationId) = row[1],
              case let .text(roleRaw) = row[2],
              case let .text(content) = row[3],
              case let .text(createdAtStr) = row[4],
              let role = MessageRole(rawValue: roleRaw),
              let createdAt = DateFormatting.date(from: createdAtStr)
        else {
            throw StorageError.dbCorrupted("Invalid chat message row data")
        }

        return ChatMessage(
            id: id,
            conversationId: conversationId,
            role: role,
            content: content,
            createdAt: createdAt
        )
    }
}
