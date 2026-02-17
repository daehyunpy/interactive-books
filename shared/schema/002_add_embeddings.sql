-- 002_add_embeddings.sql
-- Enable sqlite-vec extension for vector storage.
-- Per-provider virtual tables (embeddings_{provider}_{dimension}) are created
-- dynamically by EmbeddingRepository.ensure_table(), not by this migration.

-- No DDL statements needed — the Database class loads the sqlite-vec extension
-- before running migrations. This file serves as a version marker.
SELECT 1;
