import Foundation
import SQLite3

public enum SQLiteValue: Sendable, Equatable {
    case text(String)
    case integer(Int)
    case real(Double)
    case null

    var textValue: String? {
        if case let .text(string) = self { return string }
        return nil
    }

    var integerValue: Int? {
        if case let .integer(value) = self { return value }
        return nil
    }
}

public final class Database: @unchecked Sendable {
    private var db: OpaquePointer?

    private nonisolated(unsafe) static let migrationPattern = /^(\d{3,})_.+\.sql$/

    public init(path: String) throws {
        guard sqlite3_open(path, &db) == SQLITE_OK else {
            let message = db.flatMap { String(cString: sqlite3_errmsg($0)) } ?? "Unknown error"
            throw StorageError.dbCorrupted("Failed to open database: \(message)")
        }
        try execute(sql: "PRAGMA journal_mode=WAL")
        try execute(sql: "PRAGMA foreign_keys=ON")
    }

    public func close() {
        if let db {
            sqlite3_close(db)
        }
        db = nil
    }

    deinit {
        close()
    }

    // MARK: - SQL Execution

    @discardableResult
    public func execute(sql: String) throws -> [[SQLiteValue]] {
        try query(sql: sql)
    }

    public func query(sql: String, bind: [SQLiteValue] = []) throws -> [[SQLiteValue]] {
        let prepared = try prepare(sql: sql)
        defer { sqlite3_finalize(prepared) }

        try bindParameters(stmt: prepared, values: bind)

        var rows: [[SQLiteValue]] = []
        while sqlite3_step(prepared) == SQLITE_ROW {
            rows.append(extractRow(stmt: prepared))
        }
        return rows
    }

    public func run(sql: String, bind: [SQLiteValue] = []) throws {
        let prepared = try prepare(sql: sql)
        defer { sqlite3_finalize(prepared) }

        try bindParameters(stmt: prepared, values: bind)

        let result = sqlite3_step(prepared)
        guard result == SQLITE_DONE || result == SQLITE_ROW else {
            throw storageError(message: "Failed to execute: \(sql)")
        }
    }

    // MARK: - Transactions

    public func transaction<T>(_ body: () throws -> T) throws -> T {
        try execute(sql: "BEGIN TRANSACTION")
        do {
            let result = try body()
            try execute(sql: "COMMIT")
            return result
        } catch {
            _ = try? execute(sql: "ROLLBACK")
            throw error
        }
    }

    // MARK: - Migrations

    public func runMigrations(schemaDir: String) throws {
        try ensureMigrationTable()
        let applied = try getAppliedVersions()

        for (path, version) in try sortedMigrationFiles(in: schemaDir) where !applied.contains(version) {
            try applyMigration(path: path, version: version)
        }
    }

    private func ensureMigrationTable() throws {
        try execute(sql: """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
    }

    private func getAppliedVersions() throws -> Set<Int> {
        let rows = try query(sql: "SELECT version FROM schema_migrations")
        return Set(rows.compactMap(\.first?.integerValue))
    }

    private func sortedMigrationFiles(in dir: String) throws -> [(path: String, version: Int)] {
        let fileManager = FileManager.default
        guard let entries = try? fileManager.contentsOfDirectory(atPath: dir) else {
            return []
        }

        return entries.compactMap { name -> (String, Int)? in
            guard let match = name.wholeMatch(of: Self.migrationPattern),
                  let version = Int(match.1)
            else {
                return nil
            }
            return ("\(dir)/\(name)", version)
        }.sorted { $0.version < $1.version }
    }

    private func applyMigration(path: String, version: Int) throws {
        let name = (path as NSString).lastPathComponent
        guard let sql = try? String(contentsOfFile: path, encoding: .utf8) else {
            throw StorageError.migrationFailed("Cannot read migration file: \(name)")
        }

        guard sqlite3_exec(db, sql, nil, nil, nil) == SQLITE_OK else {
            throw StorageError.migrationFailed(
                "Migration '\(name)' failed: \(errorMessage)",
            )
        }

        try run(
            sql: "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
            bind: [.integer(version), .text(name)],
        )
    }

    // MARK: - Helpers

    private func prepare(sql: String) throws -> OpaquePointer {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK,
              let prepared = stmt
        else {
            throw storageError(message: "Failed to prepare: \(sql)")
        }
        return prepared
    }

    private func bindParameters(stmt: OpaquePointer, values: [SQLiteValue]) throws {
        for (index, value) in values.enumerated() {
            let position = Int32(index + 1)
            let result: Int32 = switch value {
                case let .text(string):
                    sqlite3_bind_text(
                        stmt, position, string, -1,
                        unsafeBitCast(-1, to: sqlite3_destructor_type.self),
                    )
                case let .integer(int):
                    sqlite3_bind_int64(stmt, position, Int64(int))
                case let .real(double):
                    sqlite3_bind_double(stmt, position, double)
                case .null:
                    sqlite3_bind_null(stmt, position)
            }
            guard result == SQLITE_OK else {
                throw storageError(message: "Failed to bind parameter at index \(index)")
            }
        }
    }

    private func extractRow(stmt: OpaquePointer) -> [SQLiteValue] {
        let count = Int(sqlite3_column_count(stmt))
        var row: [SQLiteValue] = []
        row.reserveCapacity(count)
        for col in 0 ..< Int32(count) {
            switch sqlite3_column_type(stmt, col) {
                case SQLITE_TEXT:
                    row.append(.text(String(cString: sqlite3_column_text(stmt, col))))
                case SQLITE_INTEGER:
                    row.append(.integer(Int(sqlite3_column_int64(stmt, col))))
                case SQLITE_FLOAT:
                    row.append(.real(sqlite3_column_double(stmt, col)))
                default:
                    row.append(.null)
            }
        }
        return row
    }

    private var errorMessage: String {
        db.flatMap { String(cString: sqlite3_errmsg($0)) } ?? "Unknown error"
    }

    private func storageError(message: String) -> StorageError {
        .writeFailed("\(message): \(errorMessage)")
    }
}
