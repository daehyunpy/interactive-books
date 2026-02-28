import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("SQLiteChunkRepository.saveChunks and getByBook")
struct ChunkRepositorySaveTests {
    @Test("saves multiple chunks and retrieves them ordered by chunk_index")
    func saveAndRetrieveOrdered() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let chunkRepo = SQLiteChunkRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let chunks = try [
            Chunk(id: "c2", bookId: "b1", content: "Second", startPage: 2, endPage: 2, chunkIndex: 1),
            Chunk(id: "c1", bookId: "b1", content: "First", startPage: 1, endPage: 1, chunkIndex: 0),
        ]
        try chunkRepo.saveChunks(bookId: "b1", chunks: chunks)

        let retrieved = try chunkRepo.getByBook("b1")
        #expect(retrieved.count == 2)
        #expect(retrieved[0].id == "c1")
        #expect(retrieved[0].chunkIndex == 0)
        #expect(retrieved[1].id == "c2")
        #expect(retrieved[1].chunkIndex == 1)
    }
}

@Suite("SQLiteChunkRepository.getUpToPage")
struct ChunkRepositoryGetUpToPageTests {
    @Test("returns only chunks where start_page <= page")
    func filtersbyPage() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let chunkRepo = SQLiteChunkRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let chunks = try [
            Chunk(id: "c1", bookId: "b1", content: "Page 1", startPage: 1, endPage: 1, chunkIndex: 0),
            Chunk(id: "c2", bookId: "b1", content: "Page 2", startPage: 2, endPage: 3, chunkIndex: 1),
            Chunk(id: "c3", bookId: "b1", content: "Page 5", startPage: 5, endPage: 6, chunkIndex: 2),
        ]
        try chunkRepo.saveChunks(bookId: "b1", chunks: chunks)

        let upTo3 = try chunkRepo.getUpToPage(bookId: "b1", page: 3)
        #expect(upTo3.count == 2)
        #expect(upTo3[0].id == "c1")
        #expect(upTo3[1].id == "c2")

        let upTo1 = try chunkRepo.getUpToPage(bookId: "b1", page: 1)
        #expect(upTo1.count == 1)
        #expect(upTo1[0].id == "c1")
    }
}

@Suite("SQLiteChunkRepository.countByBook")
struct ChunkRepositoryCountTests {
    @Test("returns correct count")
    func countsChunks() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let chunkRepo = SQLiteChunkRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Test Book"))

        let chunks = try [
            Chunk(id: "c1", bookId: "b1", content: "A", startPage: 1, endPage: 1, chunkIndex: 0),
            Chunk(id: "c2", bookId: "b1", content: "B", startPage: 2, endPage: 2, chunkIndex: 1),
        ]
        try chunkRepo.saveChunks(bookId: "b1", chunks: chunks)

        #expect(try chunkRepo.countByBook("b1") == 2)
    }

    @Test("returns 0 for book with no chunks")
    func zeroForEmptyBook() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }

        let chunkRepo = SQLiteChunkRepository(database: db)
        #expect(try chunkRepo.countByBook("nonexistent") == 0)
    }
}

@Suite("SQLiteChunkRepository.deleteByBook")
struct ChunkRepositoryDeleteTests {
    @Test("deletes all chunks for a book, other books unaffected")
    func deletesOnlyTargetBook() throws {
        let db = try StorageTestHelper.createTestDatabase()
        defer { db.close() }
        let bookRepo = SQLiteBookRepository(database: db)
        let chunkRepo = SQLiteChunkRepository(database: db)

        try bookRepo.save(Book(id: "b1", title: "Book 1"))
        try bookRepo.save(Book(id: "b2", title: "Book 2"))

        try chunkRepo.saveChunks(bookId: "b1", chunks: [
            Chunk(id: "c1", bookId: "b1", content: "A", startPage: 1, endPage: 1, chunkIndex: 0),
        ])
        try chunkRepo.saveChunks(bookId: "b2", chunks: [
            Chunk(id: "c2", bookId: "b2", content: "B", startPage: 1, endPage: 1, chunkIndex: 0),
        ])

        try chunkRepo.deleteByBook("b1")

        #expect(try chunkRepo.countByBook("b1") == 0)
        #expect(try chunkRepo.countByBook("b2") == 1)
    }
}
