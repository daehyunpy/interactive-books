public protocol EmbeddingProvider: Sendable {
    var providerName: String { get }
    var dimension: Int { get }
    func embed(texts: [String]) async throws -> [[Float]]
}
