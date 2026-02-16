## Why

Phase 4 embedded all book chunks into sqlite-vec virtual tables. But the embeddings are inert — there's no way to query them. Phase 5 adds vector similarity search so that given a user's question, we can find the most relevant chunks. This is the core retrieval step in the RAG pipeline, and it must support page-scoped filtering (no spoilers beyond the reader's current page).

## What Changes

- Add a `SearchResult` domain value object (chunk reference + distance score)
- Add a `search` method to the `EmbeddingRepository` protocol for KNN vector search
- Implement sqlite-vec KNN search in the existing `EmbeddingRepository` adapter
- Add a `SearchBooksUseCase` in `app/search.py` that embeds the query, searches vectors, and returns ranked chunks with page filtering
- Wire a `cli search <book-id> <query>` command that prints retrieved chunks with scores and page numbers
- Support configurable top-k (default: 5) and optional page filtering via `current_page`

## Capabilities

### New Capabilities
- `vector-search`: KNN search protocol, sqlite-vec search adapter, SearchResult value object
- `search-pipeline`: SearchBooksUseCase orchestration, CLI search command, page filtering

### Modified Capabilities
- `embedding-storage`: Add `search` method to EmbeddingRepository protocol and sqlite-vec adapter
- `repository-protocols`: Add SearchResult to domain types used in protocols

## Impact

- `domain/protocols.py` — add `search` to `EmbeddingRepository`
- `domain/search_result.py` — new value object
- `infra/storage/embedding_repo.py` — implement KNN search with partition key + page join
- `app/search.py` — new use case
- `main.py` — new `search` CLI command
- Dependencies: no new dependencies (sqlite-vec and openai already installed)
