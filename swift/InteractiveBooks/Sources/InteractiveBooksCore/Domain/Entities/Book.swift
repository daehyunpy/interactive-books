import Foundation

public enum BookStatus: String, Sendable, Equatable {
    case pending
    case ingesting
    case ready
    case failed
}

public final class Book: @unchecked Sendable, Equatable {
    public let id: String
    public private(set) var title: String
    public private(set) var status: BookStatus
    public private(set) var currentPage: Int
    public private(set) var embeddingProvider: String?
    public private(set) var embeddingDimension: Int?
    public let createdAt: Date
    public private(set) var updatedAt: Date

    public init(
        id: String,
        title: String,
        status: BookStatus = .pending,
        currentPage: Int = 0,
        embeddingProvider: String? = nil,
        embeddingDimension: Int? = nil,
        createdAt: Date = .now,
        updatedAt: Date = .now,
    ) throws {
        guard !title.trimmingCharacters(in: .whitespaces).isEmpty else {
            throw BookError.invalidState("Book title cannot be empty")
        }
        self.id = id
        self.title = title
        self.status = status
        self.currentPage = currentPage
        self.embeddingProvider = embeddingProvider
        self.embeddingDimension = embeddingDimension
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    public func startIngestion() throws {
        guard status == .pending else {
            throw BookError.invalidState(
                "Cannot start ingestion from '\(status.rawValue)' status",
            )
        }
        status = .ingesting
    }

    public func completeIngestion() throws {
        guard status == .ingesting else {
            throw BookError.invalidState(
                "Cannot complete ingestion from '\(status.rawValue)' status",
            )
        }
        status = .ready
    }

    public func failIngestion() throws {
        guard status == .ingesting else {
            throw BookError.invalidState(
                "Cannot fail ingestion from '\(status.rawValue)' status",
            )
        }
        status = .failed
    }

    public func resetToPending() {
        status = .pending
    }

    public func setCurrentPage(_ page: Int) throws {
        guard page >= 0 else {
            throw BookError.invalidState(
                "Current page cannot be negative: \(page)",
            )
        }
        currentPage = page
    }

    public func switchEmbeddingProvider(provider: String, dimension: Int) {
        embeddingProvider = provider
        embeddingDimension = dimension
        resetToPending()
    }

    package init(
        fromRow id: String,
        title: String,
        status: BookStatus,
        currentPage: Int,
        embeddingProvider: String?,
        embeddingDimension: Int?,
        createdAt: Date,
        updatedAt: Date,
    ) {
        self.id = id
        self.title = title
        self.status = status
        self.currentPage = currentPage
        self.embeddingProvider = embeddingProvider
        self.embeddingDimension = embeddingDimension
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    public static func == (lhs: Book, rhs: Book) -> Bool {
        lhs.id == rhs.id
    }
}
