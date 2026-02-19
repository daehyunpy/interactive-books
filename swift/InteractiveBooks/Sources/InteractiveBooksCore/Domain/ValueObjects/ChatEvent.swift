public enum ChatEvent: @unchecked Sendable {
    case toolInvocation(name: String, arguments: [String: Any])
    case toolResult(query: String, resultCount: Int, results: [SearchResult])
    case tokenUsage(inputTokens: Int, outputTokens: Int)
}
