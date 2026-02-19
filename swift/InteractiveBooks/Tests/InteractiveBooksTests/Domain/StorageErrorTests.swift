@testable import InteractiveBooksCore
import Testing

@Suite("StorageError")
struct StorageErrorTests {
    @Test("each case preserves its message")
    func eachCasePreservesMessage() {
        #expect(StorageError.dbCorrupted("a") != StorageError.dbCorrupted("b"))
        #expect(StorageError.migrationFailed("a") != StorageError.migrationFailed("b"))
        #expect(StorageError.writeFailed("a") != StorageError.writeFailed("b"))
        #expect(StorageError.notFound("a") != StorageError.notFound("b"))
    }

    @Test("different cases are not equal")
    func differentCasesAreNotEqual() {
        #expect(StorageError.dbCorrupted("x") != StorageError.notFound("x"))
    }
}
