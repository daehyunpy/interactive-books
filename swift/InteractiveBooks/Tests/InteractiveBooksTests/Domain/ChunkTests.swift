import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("Chunk creation")
struct ChunkCreationTests {
    @Test("valid chunk creates successfully")
    func validChunkCreates() throws {
        let chunk = try Chunk(
            id: "c1",
            bookId: "b1",
            content: "Some content",
            startPage: 1,
            endPage: 2,
            chunkIndex: 0,
        )
        #expect(chunk.id == "c1")
        #expect(chunk.bookId == "b1")
        #expect(chunk.content == "Some content")
        #expect(chunk.startPage == 1)
        #expect(chunk.endPage == 2)
        #expect(chunk.chunkIndex == 0)
    }

    @Test("startPage less than 1 throws")
    func startPageLessThanOneThrows() {
        #expect(throws: BookError.self) {
            try Chunk(
                id: "c1", bookId: "b1", content: "text",
                startPage: 0, endPage: 1, chunkIndex: 0,
            )
        }
    }

    @Test("endPage less than startPage throws")
    func endPageLessThanStartPageThrows() {
        #expect(throws: BookError.self) {
            try Chunk(
                id: "c1", bookId: "b1", content: "text",
                startPage: 3, endPage: 2, chunkIndex: 0,
            )
        }
    }
}

@Suite("Chunk Equatable")
struct ChunkEquatableTests {
    @Test("equal by all fields")
    func equalByAllFields() throws {
        let date = Date()
        let chunk1 = try Chunk(
            id: "c1", bookId: "b1", content: "text",
            startPage: 1, endPage: 1, chunkIndex: 0, createdAt: date,
        )
        let chunk2 = try Chunk(
            id: "c1", bookId: "b1", content: "text",
            startPage: 1, endPage: 1, chunkIndex: 0, createdAt: date,
        )
        #expect(chunk1 == chunk2)
    }

    @Test("not equal with different content")
    func notEqualWithDifferentContent() throws {
        let date = Date()
        let chunk1 = try Chunk(
            id: "c1", bookId: "b1", content: "text A",
            startPage: 1, endPage: 1, chunkIndex: 0, createdAt: date,
        )
        let chunk2 = try Chunk(
            id: "c1", bookId: "b1", content: "text B",
            startPage: 1, endPage: 1, chunkIndex: 0, createdAt: date,
        )
        #expect(chunk1 != chunk2)
    }
}
