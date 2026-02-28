import ArgumentParser
import Foundation
import InteractiveBooksCore

struct BooksCommand: ParsableCommand {
    static let configuration = CommandConfiguration(
        commandName: "books",
        abstract: "List all books in the library"
    )

    func run() throws {
        let database = try openDatabase()
        defer { database.close() }

        let bookRepo = SQLiteBookRepository(database: database)
        let chunkRepo = SQLiteChunkRepository(database: database)
        let books = try bookRepo.getAll()

        guard !books.isEmpty else {
            print("No books found.")
            return
        }

        try printBookTable(books: books, chunkRepo: chunkRepo)
    }

    private func openDatabase() throws -> Database {
        let projectRoot = resolveProjectRoot()
        let dataDir = "\(projectRoot)/data"
        if !FileManager.default.fileExists(atPath: dataDir) {
            try FileManager.default.createDirectory(
                atPath: dataDir, withIntermediateDirectories: true
            )
        }

        let database = try Database(path: "\(dataDir)/books.db")
        try database.runMigrations(schemaDir: "\(projectRoot)/shared/schema")
        return database
    }

    private func printBookTable(books: [Book], chunkRepo: SQLiteChunkRepository) throws {
        let header = String(
            format: "%-36s  %-30s  %-10s  %6s  %4s",
            "ID", "Title", "Status", "Chunks", "Page"
        )
        print(header)
        print(String(repeating: "─", count: header.count))

        for book in books {
            let chunkCount = try chunkRepo.countByBook(book.id)
            let titleDisplay = book.title.count > 30
                ? String(book.title.prefix(27)) + "..."
                : book.title
            print(String(
                format: "%-36s  %-30s  %-10s  %6d  %4d",
                book.id,
                titleDisplay,
                book.status.rawValue,
                chunkCount,
                book.currentPage
            ))
        }
    }

    private func resolveProjectRoot() -> String {
        let cwd = FileManager.default.currentDirectoryPath
        if FileManager.default.fileExists(atPath: "\(cwd)/shared/schema") {
            return cwd
        }
        if FileManager.default.fileExists(atPath: "\(cwd)/../shared/schema") {
            return "\(cwd)/.."
        }
        return cwd
    }
}
