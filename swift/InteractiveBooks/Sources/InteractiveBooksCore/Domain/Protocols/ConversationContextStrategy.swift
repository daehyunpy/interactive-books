public protocol ConversationContextStrategy: Sendable {
    func buildContext(history: [ChatMessage]) -> [ChatMessage]
}
