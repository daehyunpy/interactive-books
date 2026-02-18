public struct PageContent: Sendable, Equatable {
    public let pageNumber: Int
    public let text: String

    public init(pageNumber: Int, text: String) throws {
        guard pageNumber >= 1 else {
            throw BookError.parseFailed(
                "Page number must be >= 1, got \(pageNumber)",
            )
        }
        self.pageNumber = pageNumber
        self.text = text
    }
}
