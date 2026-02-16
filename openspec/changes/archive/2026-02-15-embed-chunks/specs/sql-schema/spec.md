## ADDED Requirements

### Requirement: Embeddings migration file
`shared/schema/002_add_embeddings.sql` SHALL exist and load the sqlite-vec extension. The migration follows the numbered naming convention (`NNN_name.sql`). Per-book vector tables are created dynamically by the `EmbeddingRepository`, not by this migration.

#### Scenario: Migration file exists
- **WHEN** the migrations directory is listed
- **THEN** `shared/schema/002_add_embeddings.sql` is present

#### Scenario: Migration loads sqlite-vec extension
- **WHEN** the migration is executed
- **THEN** the sqlite-vec extension is loaded and available for subsequent virtual table operations
