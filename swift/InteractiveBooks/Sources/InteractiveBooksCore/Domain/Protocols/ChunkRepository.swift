public protocol ChunkRepository: Sendable {
    func saveChunks(bookId: String, chunks: [Chunk]) throws
    func getByBook(_ bookId: String) throws -> [Chunk]
    func getUpToPage(bookId: String, page: Int) throws -> [Chunk]
    func countByBook(_ bookId: String) throws -> Int
    func deleteByBook(_ bookId: String) throws
}
