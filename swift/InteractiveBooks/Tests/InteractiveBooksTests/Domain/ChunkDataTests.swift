import Testing

@testable import InteractiveBooksCore

@Suite("ChunkData")
struct ChunkDataTests {
    @Test("valid creation succeeds")
    func validCreation() throws {
        let data = try ChunkData(
            content: "Some text",
            startPage: 1,
            endPage: 2,
            chunkIndex: 0
        )
        #expect(data.content == "Some text")
        #expect(data.startPage == 1)
        #expect(data.endPage == 2)
        #expect(data.chunkIndex == 0)
    }

    @Test("empty content throws")
    func emptyContentThrows() {
        #expect(throws: BookError.self) {
            try ChunkData(content: "", startPage: 1, endPage: 1, chunkIndex: 0)
        }
    }

    @Test("startPage less than 1 throws")
    func startPageLessThanOneThrows() {
        #expect(throws: BookError.self) {
            try ChunkData(content: "text", startPage: 0, endPage: 1, chunkIndex: 0)
        }
    }

    @Test("endPage less than startPage throws")
    func endPageLessThanStartPageThrows() {
        #expect(throws: BookError.self) {
            try ChunkData(content: "text", startPage: 3, endPage: 2, chunkIndex: 0)
        }
    }

    @Test("negative chunkIndex throws")
    func negativeChunkIndexThrows() {
        #expect(throws: BookError.self) {
            try ChunkData(content: "text", startPage: 1, endPage: 1, chunkIndex: -1)
        }
    }
}
