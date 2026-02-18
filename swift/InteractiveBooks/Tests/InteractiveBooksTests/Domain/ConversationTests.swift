import Testing

@testable import InteractiveBooksCore

@Suite("Conversation creation")
struct ConversationCreationTests {
    @Test("valid title creates conversation")
    func validTitleCreates() throws {
        let conversation = try Conversation(id: "conv1", bookId: "b1", title: "Chat about Ch.1")
        #expect(conversation.title == "Chat about Ch.1")
        #expect(conversation.bookId == "b1")
    }

    @Test("empty title throws invalidState")
    func emptyTitleThrows() {
        #expect(throws: BookError.invalidState("Conversation title cannot be empty")) {
            try Conversation(id: "conv1", bookId: "b1", title: "")
        }
    }

    @Test("whitespace-only title throws invalidState")
    func whitespaceOnlyTitleThrows() {
        #expect(throws: BookError.invalidState("Conversation title cannot be empty")) {
            try Conversation(id: "conv1", bookId: "b1", title: "   ")
        }
    }
}

@Suite("Conversation.rename")
struct ConversationRenameTests {
    @Test("valid rename succeeds")
    func validRenameSucceeds() throws {
        let conversation = try Conversation(id: "conv1", bookId: "b1", title: "Original")
        try conversation.rename(to: "Updated")
        #expect(conversation.title == "Updated")
    }

    @Test("empty title rename throws")
    func emptyTitleRenameThrows() throws {
        let conversation = try Conversation(id: "conv1", bookId: "b1", title: "Original")
        #expect(throws: BookError.invalidState("Conversation title cannot be empty")) {
            try conversation.rename(to: "")
        }
    }
}

@Suite("Conversation Equatable")
struct ConversationEquatableTests {
    @Test("equal by id only")
    func equalByIdOnly() throws {
        let conv1 = try Conversation(id: "conv1", bookId: "b1", title: "Title A")
        let conv2 = try Conversation(id: "conv1", bookId: "b2", title: "Title B")
        #expect(conv1 == conv2)
    }

    @Test("not equal with different ids")
    func notEqualWithDifferentIds() throws {
        let conv1 = try Conversation(id: "conv1", bookId: "b1", title: "Same")
        let conv2 = try Conversation(id: "conv2", bookId: "b1", title: "Same")
        #expect(conv1 != conv2)
    }
}
