public protocol EmbeddingRepository: Sendable {
    func ensureTable(providerName: String, dimension: Int) throws
    func saveEmbeddings(
        providerName: String,
        dimension: Int,
        bookId: String,
        embeddings: [EmbeddingVector],
    ) throws
    func deleteByBook(providerName: String, dimension: Int, bookId: String) throws
    func hasEmbeddings(bookId: String, providerName: String, dimension: Int) throws -> Bool
    func search(
        providerName: String,
        dimension: Int,
        bookId: String,
        queryVector: [Float],
        topK: Int,
    ) throws -> [(chunkId: String, distance: Float)]
}
