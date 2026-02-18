import Foundation

public struct Chunk: Sendable, Equatable {
    public let id: String
    public let bookId: String
    public let content: String
    public let startPage: Int
    public let endPage: Int
    public let chunkIndex: Int
    public let createdAt: Date

    public init(
        id: String,
        bookId: String,
        content: String,
        startPage: Int,
        endPage: Int,
        chunkIndex: Int,
        createdAt: Date = .now,
    ) throws {
        guard startPage >= 1 else {
            throw BookError.invalidState(
                "Chunk start_page must be >= 1, got \(startPage)",
            )
        }
        guard endPage >= startPage else {
            throw BookError.invalidState(
                "Chunk end_page (\(endPage)) must be >= start_page (\(startPage))",
            )
        }
        self.id = id
        self.bookId = bookId
        self.content = content
        self.startPage = startPage
        self.endPage = endPage
        self.chunkIndex = chunkIndex
        self.createdAt = createdAt
    }
}
