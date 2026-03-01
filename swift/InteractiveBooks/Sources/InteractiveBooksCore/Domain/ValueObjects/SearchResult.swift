public struct SearchResult: Sendable, Equatable {
    public let chunkId: String
    public let content: String
    public let startPage: Int
    public let endPage: Int
    public let distance: Float

    public init(
        chunkId: String,
        content: String,
        startPage: Int,
        endPage: Int,
        distance: Float
    ) {
        self.chunkId = chunkId
        self.content = content
        self.startPage = startPage
        self.endPage = endPage
        self.distance = distance
    }
}
