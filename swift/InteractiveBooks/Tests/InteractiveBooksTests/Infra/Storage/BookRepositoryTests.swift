import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("SQLiteBookRepository.save and get")
struct BookRepositorySaveTests {
    @Test("saves a book and retrieves it with matching fields")
    func saveAndRetrieve() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let book = try Book(
            id: "b1", title: "Test Book", status: .ready,
            currentPage: 5, embeddingProvider: "openai", embeddingDimension: 1536,
            createdAt: StorageTestHelper.fixedDate, updatedAt: StorageTestHelper.fixedDate2
        )
        try repo.save(book)

        let retrieved = try repo.get("b1")
        #expect(retrieved != nil)
        #expect(retrieved?.id == "b1")
        #expect(retrieved?.title == "Test Book")
        #expect(retrieved?.status == .ready)
        #expect(retrieved?.currentPage == 5)
        #expect(retrieved?.embeddingProvider == "openai")
        #expect(retrieved?.embeddingDimension == 1536)
    }
}

@Suite("SQLiteBookRepository.save upsert")
struct BookRepositoryUpsertTests {
    @Test("saving with same ID updates fields")
    func upsertUpdatesFields() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let book = try Book(
            id: "b1", title: "Original",
            createdAt: StorageTestHelper.fixedDate, updatedAt: StorageTestHelper.fixedDate
        )
        try repo.save(book)

        try book.startIngestion()
        try repo.save(book)

        let retrieved = try repo.get("b1")
        #expect(retrieved?.title == "Original")
        #expect(retrieved?.status == .ingesting)
    }
}

@Suite("SQLiteBookRepository.get")
struct BookRepositoryGetTests {
    @Test("returns nil for non-existent book ID")
    func nonExistentReturnsNil() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let result = try repo.get("nonexistent")
        #expect(result == nil)
    }
}

@Suite("SQLiteBookRepository.getAll")
struct BookRepositoryGetAllTests {
    @Test("returns all saved books")
    func returnsAllBooks() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let book1 = try Book(id: "b1", title: "First Book")
        let book2 = try Book(id: "b2", title: "Second Book")
        try repo.save(book1)
        try repo.save(book2)

        let all = try repo.getAll()
        #expect(all.count == 2)
    }
}

@Suite("SQLiteBookRepository.delete")
struct BookRepositoryDeleteTests {
    @Test("deletes a book and get returns nil")
    func deleteRemovesBook() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let book = try Book(id: "b1", title: "To Delete")
        try repo.save(book)
        try repo.delete("b1")

        #expect(try repo.get("b1") == nil)
    }
}

@Suite("SQLiteBookRepository cascade delete")
struct BookRepositoryCascadeTests {
    @Test("deleting a book cascades to chunks, conversations, and messages")
    func cascadeDelete() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let chunkRepo = SQLiteChunkRepository(database: db)
        let convRepo = SQLiteConversationRepository(database: db)
        let msgRepo = SQLiteChatMessageRepository(database: db)

        let book = try Book(id: "b1", title: "Book With Data")
        try bookRepo.save(book)

        let chunk = try Chunk(
            id: "c1", bookId: "b1", content: "text",
            startPage: 1, endPage: 1, chunkIndex: 0
        )
        try chunkRepo.saveChunks(bookId: "b1", chunks: [chunk])

        let conv = try Conversation(id: "conv1", bookId: "b1", title: "Chat")
        try convRepo.save(conv)

        let msg = ChatMessage(
            id: "m1", conversationId: "conv1", role: .user, content: "Hello"
        )
        try msgRepo.save(msg)

        // Delete the book — everything should cascade
        try bookRepo.delete("b1")

        #expect(try chunkRepo.countByBook("b1") == 0)
        #expect(try convRepo.getByBook("b1").isEmpty)
        #expect(try msgRepo.getByConversation("conv1").isEmpty)
    }
}

@Suite("SQLiteBookRepository nullable fields")
struct BookRepositoryNullableTests {
    @Test("saves and retrieves book with nil embedding fields")
    func nilEmbeddingFields() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let repo = SQLiteBookRepository(database: db)

        let book = try Book(id: "b1", title: "No Embeddings")
        try repo.save(book)

        let retrieved = try repo.get("b1")
        #expect(retrieved?.embeddingProvider == nil)
        #expect(retrieved?.embeddingDimension == nil)
    }
}
