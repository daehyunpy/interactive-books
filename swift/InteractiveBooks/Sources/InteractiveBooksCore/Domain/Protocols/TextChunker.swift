public protocol TextChunker: Sendable {
    func chunk(pages: [PageContent]) throws -> [ChunkData]
}
