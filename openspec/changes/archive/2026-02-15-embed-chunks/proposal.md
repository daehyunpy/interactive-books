## Why

Phase 3 ingests books into chunks but those chunks have no vector representations. Without embeddings, the retrieval pipeline (Phase 5) has nothing to search against. This phase adds the ability to generate embedding vectors for each chunk and store them in sqlite-vec, completing the data pipeline needed for semantic search.

## What Changes

- Add `EmbeddingProvider` protocol to the domain layer defining `embed(texts: list[str]) → list[list[float]]` and metadata properties (provider name, dimension)
- Add `EmbeddingVector` domain value object holding the vector data with its chunk reference
- Add `EmbeddingRepository` protocol for storing and retrieving vectors
- Implement OpenAI embedding adapter as the first provider (simplest SDK, one-line call per the technical design)
- Add `002_add_embeddings.sql` migration creating per-book virtual tables via sqlite-vec
- Implement sqlite-vec storage adapter for embedding persistence
- Add `EmbedBookUseCase` in the application layer orchestrating: load chunks → batch embed → store vectors → update book metadata
- Wire `embed` CLI command for prototyping and debugging
- Add `EMBEDDING_FAILED` error code to `BookErrorCode` for embedding-specific failures

## Capabilities

### New Capabilities

- `embedding-provider`: Domain protocol and OpenAI adapter for generating text embeddings
- `embedding-storage`: sqlite-vec schema, migration, and repository for vector persistence
- `embed-pipeline`: Application use case orchestrating chunk embedding and CLI command

### Modified Capabilities

- `sql-schema`: Adding `002_add_embeddings.sql` migration for sqlite-vec extension loading
- `domain-errors`: Adding `EMBEDDING_FAILED` error code to `BookErrorCode`

## Impact

- **New dependency**: `openai` Python SDK for the OpenAI embedding adapter
- **New dependency**: `sqlite-vec` Python package for vector storage
- **Schema change**: New migration file `002_add_embeddings.sql` — per-book virtual tables
- **Domain error change**: `BookErrorCode` gains `EMBEDDING_FAILED` case
- **Protocols**: New `EmbeddingProvider` and `EmbeddingRepository` in `domain/protocols.py`
- **CLI**: New `embed` command in `main.py`
