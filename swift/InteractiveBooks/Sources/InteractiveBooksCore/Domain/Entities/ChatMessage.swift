import Foundation

public enum MessageRole: String, Sendable, Equatable {
    case user
    case assistant
    case toolResult = "tool_result"
}

public struct ChatMessage: Sendable, Equatable {
    public let id: String
    public let conversationId: String
    public let role: MessageRole
    public let content: String
    public let createdAt: Date

    public init(
        id: String,
        conversationId: String,
        role: MessageRole,
        content: String,
        createdAt: Date = .now,
    ) {
        self.id = id
        self.conversationId = conversationId
        self.role = role
        self.content = content
        self.createdAt = createdAt
    }
}
