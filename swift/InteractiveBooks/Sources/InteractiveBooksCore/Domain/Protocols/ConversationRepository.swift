public protocol ConversationRepository: Sendable {
    func save(_ conversation: Conversation) throws
    func get(_ conversationId: String) throws -> Conversation?
    func getByBook(_ bookId: String) throws -> [Conversation]
    func delete(_ conversationId: String) throws
}
