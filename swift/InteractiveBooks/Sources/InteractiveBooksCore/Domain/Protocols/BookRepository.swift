public protocol BookRepository: Sendable {
    func save(_ book: Book) throws
    func get(_ bookId: String) throws -> Book?
    func getAll() throws -> [Book]
    func delete(_ bookId: String) throws
}
