public struct BookSummary: Sendable, Equatable {
    public let id: String
    public let title: String
    public let status: BookStatus
    public let chunkCount: Int
    public let embeddingProvider: String?
    public let currentPage: Int

    public init(
        id: String,
        title: String,
        status: BookStatus,
        chunkCount: Int,
        embeddingProvider: String?,
        currentPage: Int
    ) {
        self.id = id
        self.title = title
        self.status = status
        self.chunkCount = chunkCount
        self.embeddingProvider = embeddingProvider
        self.currentPage = currentPage
    }
}
