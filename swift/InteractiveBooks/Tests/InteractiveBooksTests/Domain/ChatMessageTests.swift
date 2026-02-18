import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("MessageRole")
struct MessageRoleTests {
    @Test("raw values match Python")
    func rawValuesMatchPython() {
        #expect(MessageRole.user.rawValue == "user")
        #expect(MessageRole.assistant.rawValue == "assistant")
        #expect(MessageRole.toolResult.rawValue == "tool_result")
    }
}

@Suite("ChatMessage creation")
struct ChatMessageCreationTests {
    @Test("creates with all fields")
    func createsWithAllFields() {
        let message = ChatMessage(
            id: "m1",
            conversationId: "conv1",
            role: .user,
            content: "Hello",
        )
        #expect(message.id == "m1")
        #expect(message.conversationId == "conv1")
        #expect(message.role == .user)
        #expect(message.content == "Hello")
    }
}

@Suite("ChatMessage Equatable")
struct ChatMessageEquatableTests {
    @Test("equal by all fields")
    func equalByAllFields() {
        let date = Date()
        let msg1 = ChatMessage(
            id: "m1", conversationId: "conv1",
            role: .user, content: "Hello", createdAt: date,
        )
        let msg2 = ChatMessage(
            id: "m1", conversationId: "conv1",
            role: .user, content: "Hello", createdAt: date,
        )
        #expect(msg1 == msg2)
    }

    @Test("not equal with different content")
    func notEqualWithDifferentContent() {
        let date = Date()
        let msg1 = ChatMessage(
            id: "m1", conversationId: "conv1",
            role: .user, content: "Hello", createdAt: date,
        )
        let msg2 = ChatMessage(
            id: "m1", conversationId: "conv1",
            role: .user, content: "World", createdAt: date,
        )
        #expect(msg1 != msg2)
    }
}
