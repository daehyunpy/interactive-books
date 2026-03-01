public protocol RetrievalStrategy: Sendable {
    func execute(
        chatProvider: any ChatProvider,
        messages: [PromptMessage],
        tools: [ToolDefinition],
        searchFn: @Sendable (String) -> [SearchResult],
        onEvent: (@Sendable (ChatEvent) -> Void)?
    ) async throws -> (String, [ChatMessage])
}
