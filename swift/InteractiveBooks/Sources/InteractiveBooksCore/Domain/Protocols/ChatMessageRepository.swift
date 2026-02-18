public protocol ChatMessageRepository: Sendable {
    func save(_ message: ChatMessage) throws
    func getByConversation(_ conversationId: String) throws -> [ChatMessage]
    func deleteByConversation(_ conversationId: String) throws
}
