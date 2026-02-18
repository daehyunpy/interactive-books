public enum StorageError: Error, Sendable, Equatable {
    case dbCorrupted(String)
    case migrationFailed(String)
    case writeFailed(String)
    case notFound(String)
}
