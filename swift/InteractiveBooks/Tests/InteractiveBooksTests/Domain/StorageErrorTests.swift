import Testing

@testable import InteractiveBooksCore

@Suite("StorageError")
struct StorageErrorTests {
    @Test("dbCorrupted carries message")
    func dbCorruptedCarriesMessage() {
        let error = StorageError.dbCorrupted("Corrupted")
        guard case let .dbCorrupted(message) = error else {
            Issue.record("Expected .dbCorrupted")
            return
        }
        #expect(message == "Corrupted")
    }

    @Test("migrationFailed carries message")
    func migrationFailedCarriesMessage() {
        let error = StorageError.migrationFailed("Migration error")
        guard case let .migrationFailed(message) = error else {
            Issue.record("Expected .migrationFailed")
            return
        }
        #expect(message == "Migration error")
    }

    @Test("writeFailed carries message")
    func writeFailedCarriesMessage() {
        let error = StorageError.writeFailed("Write error")
        guard case let .writeFailed(message) = error else {
            Issue.record("Expected .writeFailed")
            return
        }
        #expect(message == "Write error")
    }

    @Test("notFound carries message")
    func notFoundCarriesMessage() {
        let error = StorageError.notFound("Not found")
        guard case let .notFound(message) = error else {
            Issue.record("Expected .notFound")
            return
        }
        #expect(message == "Not found")
    }
}
