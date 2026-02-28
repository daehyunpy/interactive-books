import Foundation

public final class SQLiteChunkRepository: ChunkRepository, @unchecked Sendable {
    private let database: Database

    public init(database: Database) {
        self.database = database
    }

    public func saveChunks(bookId: String, chunks: [Chunk]) throws {
        try database.transaction {
            for chunk in chunks {
                try database.run(
                    sql: """
                        INSERT INTO chunks (id, book_id, content, start_page, end_page, chunk_index, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                    bind: [
                        .text(chunk.id),
                        .text(chunk.bookId),
                        .text(chunk.content),
                        .integer(chunk.startPage),
                        .integer(chunk.endPage),
                        .integer(chunk.chunkIndex),
                        .text(DateFormatting.iso8601String(from: chunk.createdAt)),
                    ]
                )
            }
        }
    }

    public func getByBook(_ bookId: String) throws -> [Chunk] {
        let rows = try database.query(
            sql: "SELECT id, book_id, content, start_page, end_page, chunk_index, created_at FROM chunks WHERE book_id = ? ORDER BY chunk_index",
            bind: [.text(bookId)]
        )
        return try rows.map { try fromRow($0) }
    }

    public func getUpToPage(bookId: String, page: Int) throws -> [Chunk] {
        let rows = try database.query(
            sql: "SELECT id, book_id, content, start_page, end_page, chunk_index, created_at FROM chunks WHERE book_id = ? AND start_page <= ? ORDER BY chunk_index",
            bind: [.text(bookId), .integer(page)]
        )
        return try rows.map { try fromRow($0) }
    }

    public func countByBook(_ bookId: String) throws -> Int {
        let rows = try database.query(
            sql: "SELECT COUNT(*) FROM chunks WHERE book_id = ?",
            bind: [.text(bookId)]
        )
        guard let row = rows.first, case let .integer(count) = row[0] else {
            return 0
        }
        return count
    }

    public func deleteByBook(_ bookId: String) throws {
        try database.run(sql: "DELETE FROM chunks WHERE book_id = ?", bind: [.text(bookId)])
    }

    private func fromRow(_ row: [SQLiteValue]) throws -> Chunk {
        guard case let .text(id) = row[0],
              case let .text(bookId) = row[1],
              case let .text(content) = row[2],
              case let .integer(startPage) = row[3],
              case let .integer(endPage) = row[4],
              case let .integer(chunkIndex) = row[5],
              case let .text(createdAtStr) = row[6],
              let createdAt = DateFormatting.date(from: createdAtStr)
        else {
            throw StorageError.dbCorrupted("Invalid chunk row data")
        }

        return Chunk(
            fromRow: id,
            bookId: bookId,
            content: content,
            startPage: startPage,
            endPage: endPage,
            chunkIndex: chunkIndex,
            createdAt: createdAt
        )
    }
}
