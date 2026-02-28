import ArgumentParser
import Foundation
import InteractiveBooksCore

struct BooksCommand: ParsableCommand {
    static let configuration = CommandConfiguration(
        commandName: "books",
        abstract: "List all books in the library"
    )

    func run() throws {
        let projectRoot = resolveProjectRoot()
        let dbPath = "\(projectRoot)/data/books.db"
        let schemaDir = "\(projectRoot)/shared/schema"

        let dataDir = "\(projectRoot)/data"
        if !FileManager.default.fileExists(atPath: dataDir) {
            try FileManager.default.createDirectory(
                atPath: dataDir, withIntermediateDirectories: true
            )
        }

        let database = try Database(path: dbPath)
        defer { database.close() }
        try database.runMigrations(schemaDir: schemaDir)

        let bookRepo = SQLiteBookRepository(database: database)
        let chunkRepo = SQLiteChunkRepository(database: database)

        let books = try bookRepo.getAll()

        guard !books.isEmpty else {
            print("No books found.")
            return
        }

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
