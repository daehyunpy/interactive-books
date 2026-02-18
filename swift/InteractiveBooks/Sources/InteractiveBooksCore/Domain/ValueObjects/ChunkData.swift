public struct ChunkData: Sendable, Equatable {
    public let content: String
    public let startPage: Int
    public let endPage: Int
    public let chunkIndex: Int

    public init(
        content: String,
        startPage: Int,
        endPage: Int,
        chunkIndex: Int
    ) throws {
        guard !content.isEmpty else {
            throw BookError.parseFailed("ChunkData content cannot be empty")
        }
        guard startPage >= 1 else {
            throw BookError.parseFailed(
                "ChunkData start_page must be >= 1, got \(startPage)"
            )
        }
        guard endPage >= startPage else {
            throw BookError.parseFailed(
                "ChunkData end_page (\(endPage)) must be >= start_page (\(startPage))"
            )
        }
        guard chunkIndex >= 0 else {
            throw BookError.parseFailed(
                "ChunkData chunk_index must be >= 0, got \(chunkIndex)"
            )
        }
        self.content = content
        self.startPage = startPage
        self.endPage = endPage
        self.chunkIndex = chunkIndex
    }
}
