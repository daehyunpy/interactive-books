public struct ChatResponse: @unchecked Sendable {
    public let text: String?
    public let toolInvocations: [ToolInvocation]
    public let usage: TokenUsage?

    public init(
        text: String? = nil,
        toolInvocations: [ToolInvocation] = [],
        usage: TokenUsage? = nil
    ) {
        self.text = text
        self.toolInvocations = toolInvocations
        self.usage = usage
    }
}
