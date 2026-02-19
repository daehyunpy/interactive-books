public struct ToolInvocation: @unchecked Sendable, Equatable {
    public let toolName: String
    public let toolUseId: String
    public let arguments: [String: Any]

    public init(toolName: String, toolUseId: String, arguments: [String: Any]) {
        self.toolName = toolName
        self.toolUseId = toolUseId
        self.arguments = arguments
    }

    public static func == (lhs: ToolInvocation, rhs: ToolInvocation) -> Bool {
        lhs.toolName == rhs.toolName && lhs.toolUseId == rhs.toolUseId
    }
}
