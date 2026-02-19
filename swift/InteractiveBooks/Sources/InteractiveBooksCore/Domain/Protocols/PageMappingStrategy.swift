public protocol PageMappingStrategy: Sendable {
    func mapPages(rawContent: String) throws -> [PageContent]
}
