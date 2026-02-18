import Testing

@testable import InteractiveBooksCore

@Suite("EmbeddingVector")
struct EmbeddingVectorTests {
    @Test("valid creation succeeds")
    func validCreation() throws {
        let vector = try EmbeddingVector(chunkId: "c1", vector: [0.1, 0.2, 0.3])
        #expect(vector.chunkId == "c1")
        #expect(vector.vector == [0.1, 0.2, 0.3])
    }

    @Test("empty vector throws")
    func emptyVectorThrows() {
        #expect(throws: BookError.self) {
            try EmbeddingVector(chunkId: "c1", vector: [])
        }
    }
}
