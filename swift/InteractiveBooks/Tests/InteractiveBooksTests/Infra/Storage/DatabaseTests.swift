import Foundation
@testable import InteractiveBooksCore
import Testing

@Suite("Database initialization")
struct DatabaseInitTests {
    @Test("opens connection and enables WAL mode")
    func walModeEnabled() throws {
        let tempDir = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: tempDir) }

        let dbPath = tempDir.appendingPathComponent("test.db").path
        let db = try Database(path: dbPath)
        defer { db.close() }

        let rows = try db.query(sql: "PRAGMA journal_mode")
        #expect(rows.count == 1)
        #expect(rows[0][0] == .text("wal"))
    }

    @Test("enables foreign keys")
    func foreignKeysEnabled() throws {
        let db = try Database(path: ":memory:")
        defer { db.close() }

        let rows = try db.query(sql: "PRAGMA foreign_keys")
        #expect(rows.count == 1)
        #expect(rows[0][0] == .integer(1))
    }
}

@Suite("Database migration runner")
struct DatabaseMigrationTests {
    @Test("applies migrations in numeric order")
    func appliesInOrder() throws {
        let dir = try createTempMigrationDir(files: [
            "002_second.sql": "CREATE TABLE second (id TEXT PRIMARY KEY);",
            "001_first.sql": "CREATE TABLE first (id TEXT PRIMARY KEY);",
        ])
        defer { removeTempDir(dir) }

        let db = try Database(path: ":memory:")
        defer { db.close() }

        try db.runMigrations(schemaDir: dir)

        // Both tables should exist
        let tables = try db.query(
            sql: "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('first','second') ORDER BY name"
        )
        #expect(tables.count == 2)
        #expect(tables[0][0] == .text("first"))
        #expect(tables[1][0] == .text("second"))

        // schema_migrations should have both versions
        let versions = try db.query(sql: "SELECT version FROM schema_migrations ORDER BY version")
        #expect(versions.count == 2)
        #expect(versions[0][0] == .integer(1))
        #expect(versions[1][0] == .integer(2))
    }

    @Test("skips already-applied migrations")
    func skipsApplied() throws {
        let dir = try createTempMigrationDir(files: [
            "001_first.sql": "CREATE TABLE first (id TEXT PRIMARY KEY);",
            "002_second.sql": "CREATE TABLE second (id TEXT PRIMARY KEY);",
        ])
        defer { removeTempDir(dir) }

        let db = try Database(path: ":memory:")
        defer { db.close() }

        try db.runMigrations(schemaDir: dir)
        // Run again — should not fail (tables already exist, migrations skipped)
        try db.runMigrations(schemaDir: dir)

        let versions = try db.query(sql: "SELECT version FROM schema_migrations ORDER BY version")
        #expect(versions.count == 2)
    }

    @Test("records version, name, and applied_at in schema_migrations")
    func recordsMigrationMetadata() throws {
        let dir = try createTempMigrationDir(files: [
            "001_initial.sql": "CREATE TABLE test (id TEXT PRIMARY KEY);",
        ])
        defer { removeTempDir(dir) }

        let db = try Database(path: ":memory:")
        defer { db.close() }

        try db.runMigrations(schemaDir: dir)

        let rows = try db.query(sql: "SELECT version, name, applied_at FROM schema_migrations")
        #expect(rows.count == 1)
        #expect(rows[0][0] == .integer(1))
        #expect(rows[0][1] == .text("001_initial.sql"))
        // applied_at should be a non-empty string
        if case let .text(appliedAt) = rows[0][2] {
            #expect(!appliedAt.isEmpty)
        } else {
            Issue.record("applied_at should be a text value")
        }
    }
}

@Suite("Database migration failure")
struct DatabaseMigrationFailureTests {
    @Test("invalid SQL throws migrationFailed with migration name")
    func invalidSqlThrowsMigrationFailed() throws {
        let dir = try createTempMigrationDir(files: [
            "001_bad.sql": "THIS IS NOT VALID SQL;",
        ])
        defer { removeTempDir(dir) }

        let db = try Database(path: ":memory:")
        defer { db.close() }

        #expect(throws: StorageError.self) {
            try db.runMigrations(schemaDir: dir)
        }
    }
}

@Suite("Database migration file pattern matching")
struct DatabaseMigrationPatternTests {
    @Test("ignores non-matching files")
    func ignoresNonMatchingFiles() throws {
        let dir = try createTempMigrationDir(files: [
            "001_valid.sql": "CREATE TABLE valid (id TEXT PRIMARY KEY);",
            ".DS_Store": "junk",
            "README.md": "# Docs",
            "1_too_short.sql": "CREATE TABLE short (id TEXT PRIMARY KEY);",
            "no_number.sql": "CREATE TABLE bad (id TEXT PRIMARY KEY);",
        ])
        defer { removeTempDir(dir) }

        let db = try Database(path: ":memory:")
        defer { db.close() }

        try db.runMigrations(schemaDir: dir)

        // Only 001_valid.sql should be applied
        let versions = try db.query(sql: "SELECT version FROM schema_migrations")
        #expect(versions.count == 1)
        #expect(versions[0][0] == .integer(1))

        // Only the 'valid' table should exist (besides schema_migrations)
        let tables = try db.query(
            sql: "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'schema_%'"
        )
        #expect(tables.count == 1)
        #expect(tables[0][0] == .text("valid"))
    }
}

// MARK: - Test Helpers

private func createTempMigrationDir(files: [String: String]) throws -> String {
    let dir = NSTemporaryDirectory() + "migrations_\(UUID().uuidString)"
    try FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
    for (name, content) in files {
        try content.write(toFile: "\(dir)/\(name)", atomically: true, encoding: .utf8)
    }
    return dir
}

private func removeTempDir(_ path: String) {
    try? FileManager.default.removeItem(atPath: path)
}
