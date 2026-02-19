@testable import InteractiveBooksCore
import Testing

@Suite("BookError")
struct BookErrorTests {
    @Test("each case preserves its message")
    func eachCasePreservesMessage() {
        // Equatable proves the message is stored — different messages produce inequality
        #expect(BookError.notFound("a") != BookError.notFound("b"))
        #expect(BookError.parseFailed("a") != BookError.parseFailed("b"))
        #expect(BookError.unsupportedFormat("a") != BookError.unsupportedFormat("b"))
        #expect(BookError.alreadyExists("a") != BookError.alreadyExists("b"))
        #expect(BookError.invalidState("a") != BookError.invalidState("b"))
        #expect(BookError.embeddingFailed("a") != BookError.embeddingFailed("b"))
        #expect(BookError.drmProtected("a") != BookError.drmProtected("b"))
        #expect(BookError.fetchFailed("a") != BookError.fetchFailed("b"))
    }

    @Test("different cases are not equal")
    func differentCasesAreNotEqual() {
        #expect(BookError.notFound("x") != BookError.parseFailed("x"))
    }
}
