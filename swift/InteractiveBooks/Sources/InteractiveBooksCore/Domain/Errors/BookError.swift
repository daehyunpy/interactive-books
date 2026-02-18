public enum BookError: Error, Sendable, Equatable {
    case notFound(String)
    case parseFailed(String)
    case unsupportedFormat(String)
    case alreadyExists(String)
    case invalidState(String)
    case embeddingFailed(String)
    case drmProtected(String)
    case fetchFailed(String)
}
