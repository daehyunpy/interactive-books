public struct EmbeddingVector: Sendable, Equatable {
    public let chunkId: String
    public let vector: [Float]

    public init(chunkId: String, vector: [Float]) throws {
        guard !vector.isEmpty else {
            throw BookError.embeddingFailed(
                "EmbeddingVector vector cannot be empty"
            )
        }
        self.chunkId = chunkId
        self.vector = vector
    }
}
