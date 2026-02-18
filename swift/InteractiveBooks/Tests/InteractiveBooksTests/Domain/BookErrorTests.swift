import Testing

@testable import InteractiveBooksCore

@Suite("BookError")
struct BookErrorTests {
    @Test("notFound carries message")
    func notFoundCarriesMessage() {
        let error = BookError.notFound("Book not found")
        guard case let .notFound(message) = error else {
            Issue.record("Expected .notFound")
            return
        }
        #expect(message == "Book not found")
    }

    @Test("parseFailed carries message")
    func parseFailedCarriesMessage() {
        let error = BookError.parseFailed("Parse error")
        guard case let .parseFailed(message) = error else {
            Issue.record("Expected .parseFailed")
            return
        }
        #expect(message == "Parse error")
    }

    @Test("unsupportedFormat carries message")
    func unsupportedFormatCarriesMessage() {
        let error = BookError.unsupportedFormat("Unknown format")
        guard case let .unsupportedFormat(message) = error else {
            Issue.record("Expected .unsupportedFormat")
            return
        }
        #expect(message == "Unknown format")
    }

    @Test("alreadyExists carries message")
    func alreadyExistsCarriesMessage() {
        let error = BookError.alreadyExists("Duplicate")
        guard case let .alreadyExists(message) = error else {
            Issue.record("Expected .alreadyExists")
            return
        }
        #expect(message == "Duplicate")
    }

    @Test("invalidState carries message")
    func invalidStateCarriesMessage() {
        let error = BookError.invalidState("Bad state")
        guard case let .invalidState(message) = error else {
            Issue.record("Expected .invalidState")
            return
        }
        #expect(message == "Bad state")
    }

    @Test("embeddingFailed carries message")
    func embeddingFailedCarriesMessage() {
        let error = BookError.embeddingFailed("Embedding error")
        guard case let .embeddingFailed(message) = error else {
            Issue.record("Expected .embeddingFailed")
            return
        }
        #expect(message == "Embedding error")
    }

    @Test("drmProtected carries message")
    func drmProtectedCarriesMessage() {
        let error = BookError.drmProtected("DRM protected")
        guard case let .drmProtected(message) = error else {
            Issue.record("Expected .drmProtected")
            return
        }
        #expect(message == "DRM protected")
    }

    @Test("fetchFailed carries message")
    func fetchFailedCarriesMessage() {
        let error = BookError.fetchFailed("Fetch error")
        guard case let .fetchFailed(message) = error else {
            Issue.record("Expected .fetchFailed")
            return
        }
        #expect(message == "Fetch error")
    }

    @Test("pattern matching works in switch")
    func patternMatchingWorks() {
        let error: BookError = .notFound("missing")
        switch error {
        case .notFound: break
        case .parseFailed, .unsupportedFormat, .alreadyExists,
             .invalidState, .embeddingFailed, .drmProtected, .fetchFailed:
            Issue.record("Expected .notFound")
        }
    }
}
