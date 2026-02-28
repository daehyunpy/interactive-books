import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("SQLiteChatMessageRepository.save and getByConversation")
struct ChatMessageRepositorySaveTests {
    @Test("saves messages with different roles and retrieves in chronological order")
    func saveAndRetrieveChronological() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)
        let msgRepo = SQLiteChatMessageRepository(database: db)

        try bookRepo.save(try Book(id: "b1", title: "Test Book"))
        try convRepo.save(try Conversation(id: "conv1", bookId: "b1", title: "Chat"))

        let msg1 = ChatMessage(
            id: "m1", conversationId: "conv1", role: .user, content: "Hello",
            createdAt: StorageTestHelper.fixedDate
        )
        let msg2 = ChatMessage(
            id: "m2", conversationId: "conv1", role: .assistant, content: "Hi there!",
            createdAt: StorageTestHelper.fixedDate2
        )
        let msg3 = ChatMessage(
            id: "m3", conversationId: "conv1", role: .toolResult, content: "{\"result\": \"data\"}",
            // swiftlint:disable:next force_unwrapping
            createdAt: StorageTestHelper.iso8601Formatter.date(from: "2025-01-17T08:00:00Z")!
        )
        try msgRepo.save(msg1)
        try msgRepo.save(msg2)
        try msgRepo.save(msg3)

        let messages = try msgRepo.getByConversation("conv1")
        #expect(messages.count == 3)
        #expect(messages[0].role == .user)
        #expect(messages[1].role == .assistant)
        #expect(messages[2].role == .toolResult)
        #expect(messages[0].content == "Hello")
        #expect(messages[1].content == "Hi there!")
    }
}

@Suite("SQLiteChatMessageRepository.getByConversation empty")
struct ChatMessageRepositoryEmptyTests {
    @Test("returns empty list for conversation with no messages")
    func emptyForNoMessages() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let msgRepo = SQLiteChatMessageRepository(database: db)

        let messages = try msgRepo.getByConversation("nonexistent")
        #expect(messages.isEmpty)
    }
}

@Suite("SQLiteChatMessageRepository.deleteByConversation")
struct ChatMessageRepositoryDeleteTests {
    @Test("deletes all messages for a conversation, other conversations unaffected")
    func deletesOnlyTargetConversation() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)
        let msgRepo = SQLiteChatMessageRepository(database: db)

        try bookRepo.save(try Book(id: "b1", title: "Test Book"))
        try convRepo.save(try Conversation(id: "conv1", bookId: "b1", title: "Chat 1"))
        try convRepo.save(try Conversation(id: "conv2", bookId: "b1", title: "Chat 2"))

        try msgRepo.save(ChatMessage(id: "m1", conversationId: "conv1", role: .user, content: "A"))
        try msgRepo.save(ChatMessage(id: "m2", conversationId: "conv2", role: .user, content: "B"))

        try msgRepo.deleteByConversation("conv1")

        #expect(try msgRepo.getByConversation("conv1").isEmpty)
        #expect(try msgRepo.getByConversation("conv2").count == 1)
    }
}
