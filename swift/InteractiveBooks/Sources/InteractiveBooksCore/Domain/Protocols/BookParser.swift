import Foundation

public protocol BookParser: Sendable {
    func parse(fileAt path: URL) async throws -> [PageContent]
}
