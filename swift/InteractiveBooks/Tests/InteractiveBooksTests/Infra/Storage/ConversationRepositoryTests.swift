import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("SQLiteConversationRepository.save and get")
struct ConversationRepositorySaveTests {
    @Test("saves a conversation and retrieves it with matching fields")
    func saveAndRetrieve() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let conv = try Conversation(
            id: "conv1", bookId: "b1", title: "My Chat",
            createdAt: StorageTestHelper.fixedDate,
        )
        try convRepo.save(conv)

        let retrieved = try convRepo.get("conv1")
        #expect(retrieved != nil)
        #expect(retrieved?.id == "conv1")
        #expect(retrieved?.bookId == "b1")
        #expect(retrieved?.title == "My Chat")
    }
}

@Suite("SQLiteConversationRepository.save upsert")
struct ConversationRepositoryUpsertTests {
    @Test("saving with same ID updates the title")
    func upsertUpdatesTitle() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let conv = try Conversation(id: "conv1", bookId: "b1", title: "Original Title")
        try convRepo.save(conv)

        try conv.rename(to: "Updated Title")
        try convRepo.save(conv)

        let retrieved = try convRepo.get("conv1")
        #expect(retrieved?.title == "Updated Title")
    }
}

@Suite("SQLiteConversationRepository.get")
struct ConversationRepositoryGetTests {
    @Test("returns nil for non-existent ID")
    func nonExistentReturnsNil() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let convRepo = SQLiteConversationRepository(database: db)

        let result = try convRepo.get("nonexistent")
        #expect(result == nil)
    }
}

@Suite("SQLiteConversationRepository.getByBook")
struct ConversationRepositoryGetByBookTests {
    @Test("returns conversations ordered by created_at DESC")
    func orderedByCreatedAtDesc() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let older = try Conversation(
            id: "conv1", bookId: "b1", title: "Older",
            createdAt: StorageTestHelper.fixedDate,
        )
        let newer = try Conversation(
            id: "conv2", bookId: "b1", title: "Newer",
            createdAt: StorageTestHelper.fixedDate2,
        )
        try convRepo.save(older)
        try convRepo.save(newer)

        let results = try convRepo.getByBook("b1")
        #expect(results.count == 2)
        #expect(results[0].id == "conv2")
        #expect(results[1].id == "conv1")
    }

    @Test("returns empty list for book with no conversations")
    func emptyForNoConversations() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let convRepo = SQLiteConversationRepository(database: db)

        let results = try convRepo.getByBook("nonexistent")
        #expect(results.isEmpty)
    }
}

@Suite("SQLiteConversationRepository.delete")
struct ConversationRepositoryDeleteTests {
    @Test("deletes the conversation and cascades to messages")
    func deleteCascadesToMessages() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)
        let msgRepo = SQLiteChatMessageRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))
        let conv = try Conversation(id: "conv1", bookId: "b1", title: "Chat")
        try convRepo.save(conv)

        let msg = ChatMessage(id: "m1", conversationId: "conv1", role: .user, content: "Hi")
        try msgRepo.save(msg)

        try convRepo.delete("conv1")

        #expect(try convRepo.get("conv1") == nil)
        #expect(try msgRepo.getByConversation("conv1").isEmpty)
    }
}
