public struct ToolDefinition: @unchecked Sendable {
    public let name: String
    public let description: String
    public let parameters: [String: Any]

    public init(name: String, description: String, parameters: [String: Any]) {
        self.name = name
        self.description = description
        self.parameters = parameters
    }
}
