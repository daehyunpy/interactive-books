import Foundation

public final class Conversation: @unchecked Sendable, Equatable {
    public let id: String
    public let bookId: String
    public private(set) var title: String
    public let createdAt: Date

    public init(
        id: String,
        bookId: String,
        title: String,
        createdAt: Date = .now,
    ) throws {
        try Self.validateTitle(title)
        self.id = id
        self.bookId = bookId
        self.title = title
        self.createdAt = createdAt
    }

    public func rename(to title: String) throws {
        try Self.validateTitle(title)
        self.title = title
    }

    private static func validateTitle(_ title: String) throws {
        guard !title.trimmingCharacters(in: .whitespaces).isEmpty else {
            throw BookError.invalidState("Conversation title cannot be empty")
        }
    }

    package init(
        fromRow id: String,
        bookId: String,
        title: String,
        createdAt: Date,
    ) {
        self.id = id
        self.bookId = bookId
        self.title = title
        self.createdAt = createdAt
    }

    public static func == (lhs: Conversation, rhs: Conversation) -> Bool {
        lhs.id == rhs.id
    }
}
