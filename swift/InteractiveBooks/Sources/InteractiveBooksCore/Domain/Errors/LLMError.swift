public enum LLMError: Error, Sendable, Equatable {
    case apiKeyMissing(String)
    case apiCallFailed(String)
    case rateLimited(String)
    case timeout(String)
    case unsupportedFeature(String)
}
