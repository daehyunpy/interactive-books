public struct PromptMessage: @unchecked Sendable, Equatable {
    public let role: String
    public let content: String
    public let toolUseId: String?
    public let toolInvocations: [ToolInvocation]

    public init(
        role: String,
        content: String,
        toolUseId: String? = nil,
        toolInvocations: [ToolInvocation] = []
    ) {
        self.role = role
        self.content = content
        self.toolUseId = toolUseId
        self.toolInvocations = toolInvocations
    }
}
