import Foundation

public final class SQLiteBookRepository: BookRepository, @unchecked Sendable {
    private let database: Database

    private static let selectColumns =
        "id, title, status, current_page, embedding_provider, embedding_dimension, created_at, updated_at"

    public init(database: Database) {
        self.database = database
    }

    public func save(_ book: Book) throws {
        try database.run(
            sql: """
                INSERT OR REPLACE INTO books
                    (\(Self.selectColumns))
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
            bind: [
                .text(book.id),
                .text(book.title),
                .text(book.status.rawValue),
                .integer(book.currentPage),
                book.embeddingProvider.map { .text($0) } ?? .null,
                book.embeddingDimension.map { .integer($0) } ?? .null,
                .text(DateFormatting.iso8601String(from: book.createdAt)),
                .text(DateFormatting.iso8601String(from: book.updatedAt)),
            ]
        )
    }

    public func get(_ bookId: String) throws -> Book? {
        let rows = try database.query(
            sql: "SELECT \(Self.selectColumns) FROM books WHERE id = ?",
            bind: [.text(bookId)]
        )
        guard let row = rows.first else { return nil }
        return try fromRow(row)
    }

    public func getAll() throws -> [Book] {
        let rows = try database.query(
            sql: "SELECT \(Self.selectColumns) FROM books"
        )
        return try rows.map { try fromRow($0) }
    }

    public func delete(_ bookId: String) throws {
        try database.run(sql: "DELETE FROM books WHERE id = ?", bind: [.text(bookId)])
    }

    private func fromRow(_ row: [SQLiteValue]) throws -> Book {
        guard case let .text(id) = row[0],
              case let .text(title) = row[1],
              case let .text(statusRaw) = row[2],
              case let .integer(currentPage) = row[3],
              case let .text(createdAtStr) = row[6],
              case let .text(updatedAtStr) = row[7],
              let status = BookStatus(rawValue: statusRaw),
              let createdAt = DateFormatting.date(from: createdAtStr),
              let updatedAt = DateFormatting.date(from: updatedAtStr)
        else {
            throw StorageError.dbCorrupted("Invalid book row data")
        }

        return Book(
            fromRow: id,
            title: title,
            status: status,
            currentPage: currentPage,
            embeddingProvider: row[4].textValue,
            embeddingDimension: row[5].integerValue,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}
