public protocol ChatProvider: Sendable {
    var modelName: String { get }
    func chat(messages: [PromptMessage]) async throws -> String
    func chatWithTools(
        messages: [PromptMessage],
        tools: [ToolDefinition]
    ) async throws -> ChatResponse
}
