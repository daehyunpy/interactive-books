import Foundation
import Testing

@testable import InteractiveBooksCore

@Suite("BookStatus")
struct BookStatusTests {
    @Test("raw values match Python")
    func rawValuesMatchPython() {
        #expect(BookStatus.pending.rawValue == "pending")
        #expect(BookStatus.ingesting.rawValue == "ingesting")
        #expect(BookStatus.ready.rawValue == "ready")
        #expect(BookStatus.failed.rawValue == "failed")
    }
}

@Suite("Book creation")
struct BookCreationTests {
    @Test("valid title creates book")
    func validTitleCreatesBook() throws {
        let book = try Book(id: "b1", title: "Test Book")
        #expect(book.title == "Test Book")
        #expect(book.status == .pending)
        #expect(book.currentPage == 0)
        #expect(book.embeddingProvider == nil)
        #expect(book.embeddingDimension == nil)
    }

    @Test("empty title throws invalidState")
    func emptyTitleThrows() {
        #expect(throws: BookError.invalidState("Book title cannot be empty")) {
            try Book(id: "b1", title: "")
        }
    }

    @Test("whitespace-only title throws invalidState")
    func whitespaceOnlyTitleThrows() {
        #expect(throws: BookError.invalidState("Book title cannot be empty")) {
            try Book(id: "b1", title: "   ")
        }
    }
}

@Suite("Book status transitions")
struct BookStatusTransitionTests {
    @Test("startIngestion from pending succeeds")
    func startIngestionFromPending() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        #expect(book.status == .ingesting)
    }

    @Test("startIngestion from ready throws")
    func startIngestionFromReadyThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.completeIngestion()
        #expect(throws: BookError.self) {
            try book.startIngestion()
        }
    }

    @Test("startIngestion from failed throws")
    func startIngestionFromFailedThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.failIngestion()
        #expect(throws: BookError.self) {
            try book.startIngestion()
        }
    }

    @Test("startIngestion from ingesting throws")
    func startIngestionFromIngestingThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        #expect(throws: BookError.self) {
            try book.startIngestion()
        }
    }

    @Test("completeIngestion from ingesting succeeds")
    func completeIngestionFromIngesting() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.completeIngestion()
        #expect(book.status == .ready)
    }

    @Test("completeIngestion from pending throws")
    func completeIngestionFromPendingThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        #expect(throws: BookError.self) {
            try book.completeIngestion()
        }
    }

    @Test("completeIngestion from ready throws")
    func completeIngestionFromReadyThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.completeIngestion()
        #expect(throws: BookError.self) {
            try book.completeIngestion()
        }
    }

    @Test("completeIngestion from failed throws")
    func completeIngestionFromFailedThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.failIngestion()
        #expect(throws: BookError.self) {
            try book.completeIngestion()
        }
    }

    @Test("failIngestion from ingesting succeeds")
    func failIngestionFromIngesting() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.failIngestion()
        #expect(book.status == .failed)
    }

    @Test("failIngestion from pending throws")
    func failIngestionFromPendingThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        #expect(throws: BookError.self) {
            try book.failIngestion()
        }
    }

    @Test("failIngestion from ready throws")
    func failIngestionFromReadyThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.completeIngestion()
        #expect(throws: BookError.self) {
            try book.failIngestion()
        }
    }

    @Test("failIngestion from failed throws")
    func failIngestionFromFailedThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.failIngestion()
        #expect(throws: BookError.self) {
            try book.failIngestion()
        }
    }

    @Test("resetToPending from any state succeeds")
    func resetToPendingFromAnyState() throws {
        let book = try Book(id: "b1", title: "Test")

        try book.startIngestion()
        try book.completeIngestion()
        #expect(book.status == .ready)
        book.resetToPending()
        #expect(book.status == .pending)

        try book.startIngestion()
        try book.failIngestion()
        #expect(book.status == .failed)
        book.resetToPending()
        #expect(book.status == .pending)

        try book.startIngestion()
        #expect(book.status == .ingesting)
        book.resetToPending()
        #expect(book.status == .pending)
    }
}

@Suite("Book.setCurrentPage")
struct BookSetCurrentPageTests {
    @Test("valid page sets current page")
    func validPageSetsCurrentPage() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.setCurrentPage(5)
        #expect(book.currentPage == 5)
    }

    @Test("zero page is valid")
    func zeroPageIsValid() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.setCurrentPage(0)
        #expect(book.currentPage == 0)
    }

    @Test("negative page throws invalidState")
    func negativePageThrows() throws {
        let book = try Book(id: "b1", title: "Test")
        #expect(throws: BookError.self) {
            try book.setCurrentPage(-1)
        }
    }
}

@Suite("Book.switchEmbeddingProvider")
struct BookSwitchEmbeddingProviderTests {
    @Test("sets provider and dimension, resets status")
    func setsProviderAndResetsStatus() throws {
        let book = try Book(id: "b1", title: "Test")
        try book.startIngestion()
        try book.completeIngestion()
        #expect(book.status == .ready)

        book.switchEmbeddingProvider(provider: "openai", dimension: 1536)
        #expect(book.embeddingProvider == "openai")
        #expect(book.embeddingDimension == 1536)
        #expect(book.status == .pending)
    }
}

@Suite("Book Equatable")
struct BookEquatableTests {
    @Test("equal by id only")
    func equalByIdOnly() throws {
        let book1 = try Book(id: "b1", title: "Title A")
        let book2 = try Book(id: "b1", title: "Title B")
        #expect(book1 == book2)
    }

    @Test("not equal with different ids")
    func notEqualWithDifferentIds() throws {
        let book1 = try Book(id: "b1", title: "Same Title")
        let book2 = try Book(id: "b2", title: "Same Title")
        #expect(book1 != book2)
    }
}
