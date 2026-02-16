## Context

Phase 3 delivered book ingestion: PDF/TXT parsing, recursive chunking, and persistence of chunks in SQLite. The `Book` aggregate already carries `embedding_provider` and `embedding_dimension` fields (set to None). The `chunks` table stores text content with page ranges. Phase 4 needs to generate embedding vectors for those chunks and store them so Phase 5 can perform vector similarity search.

The technical design specifies sqlite-vec for vector storage, OpenAI as the first embedding provider, and per-book virtual tables with dimension stored at the book level.

## Goals / Non-Goals

**Goals:**

- Define an `EmbeddingProvider` domain protocol that abstracts embedding generation
- Implement an OpenAI embedding adapter as the first provider (text-embedding-3-small, 1536 dimensions)
- Add a sqlite-vec migration (`002_add_embeddings.sql`) and storage adapter for vector persistence
- Orchestrate chunk embedding via an `EmbedBookUseCase` that batches chunks, calls the provider, and stores results
- Wire a `cli embed <book-id>` command for testing
- Track embedding status on the `Book` aggregate (provider name + dimension)

**Non-Goals:**

- Retrieval / vector search — that is Phase 5
- Multiple embedding providers (Ollama, Apple NaturalLanguage, Voyage AI) — only OpenAI for now; others come after the first end-to-end pipeline works
- Re-embedding on provider switch — the domain model already supports `switch_embedding_provider()` but the re-embed workflow is Phase 5+ scope
- Streaming or async embedding — Phase 4 runs synchronously like Phase 3
- Incremental embedding (resume from last chunk on failure) — desirable but deferred to Phase 7 polish

## Decisions

### 1. EmbeddingProvider protocol returns list[list[float]]

**Decision:** `EmbeddingProvider.embed(texts: list[str]) → list[list[float]]` takes a batch of texts and returns one vector per text. Properties `provider_name: str` and `dimension: int` expose metadata.

**Rationale:** Batch embedding is more efficient (one API call for many chunks). Returning raw float lists keeps the domain free of numpy/tensor dependencies. The provider exposes its dimension so the use case can validate and store it on the Book.

**Alternatives considered:**

- Single-text `embed(text) → list[float]`: simpler but inefficient — OpenAI supports batching natively
- Return a wrapper `EmbeddingVector` from the provider: leaks domain types into the protocol; raw floats are simpler

### 2. Per-provider virtual tables in sqlite-vec

**Decision:** Each provider/dimension combo gets one sqlite-vec virtual table named `embeddings_{provider}_{dimension}` (e.g., `embeddings_openai_1536`). The table stores `book_id`, `chunk_id`, and the vector column. All books sharing the same provider share one table.

**Rationale:** sqlite-vec requires a fixed dimension per virtual table, but the constraint is per-provider, not per-book. All books using the same provider have the same dimension. Per-provider tables mean far fewer tables (one per provider vs one per book), support standard `book_id` column for filtering and cleanup, and use a human-readable table name.

**Alternatives considered:**

- Per-book tables (`book_embeddings_{uuid_hex}`): creates many tables, unreadable names, no FK relationship, dynamic table creation on every ingest
- Single global table with a dimension column: sqlite-vec doesn't support variable-dimension vectors in one table
- Store vectors as BLOBs in the chunks table: loses sqlite-vec's optimized vector search

### 3. OpenAI text-embedding-3-small as first implementation

**Decision:** Use OpenAI's `text-embedding-3-small` model (1536 dimensions) via the `openai` Python SDK.

**Rationale:** Technical design names this as "easiest first." The SDK is simple (one function call), well-documented, and the model balances cost/quality. The OPENAI_API_KEY is already in the environment variable table.

**Alternatives considered:**

- text-embedding-3-large (3072d): higher quality but double the storage, not needed for v1
- Ollama local: requires running a separate server, more complex setup for first implementation

### 4. Batch size of 100 chunks per API call

**Decision:** Embed chunks in batches of 100. The OpenAI API supports up to 2048 inputs per call, but 100 keeps request sizes reasonable and allows progress reporting.

**Rationale:** A typical book has 50-200 chunks. Batching by 100 means 1-2 API calls for most books. Small enough to avoid timeouts, large enough to minimize round trips.

### 5. EmbeddingRepository manages per-provider table lifecycle

**Decision:** `EmbeddingRepository` protocol has methods: `ensure_table(provider_name, dimension)` (create if not exists), `save_embeddings(provider_name, dimension, embeddings)`, `delete_by_book(provider_name, dimension, book_id)`, `has_embeddings(book_id, provider_name, dimension)`. The storage adapter handles the sqlite-vec SQL.

**Rationale:** Table creation is idempotent (`ensure_table` creates only if missing). Deletion is per-book within the shared table (`DELETE WHERE book_id = ?`). This keeps the domain layer clean while supporting multiple books per table.

**Alternatives considered:**

- Expose `create_table`/`drop_table` per book: too granular, callers shouldn't manage table lifecycle directly
- Put table management in the use case: mixes infrastructure SQL with application logic

### 6. Migration adds sqlite-vec extension loading

**Decision:** `002_add_embeddings.sql` loads the sqlite-vec extension and is otherwise minimal — per-provider tables are created dynamically by the repository on first use, not by the migration.

**Rationale:** sqlite-vec virtual tables are created per-provider with a specific dimension. The first call to `ensure_table` for a given provider creates the table. The migration's role is to ensure the extension is loaded.

### 7. EmbedBookUseCase updates Book metadata

**Decision:** After successful embedding, the use case sets `book.embedding_provider` and `book.embedding_dimension` and saves the Book. It does NOT change `book.status` — the book remains `READY` (it was already READY after ingestion).

**Rationale:** Adding a new status like `EMBEDDING` would require changing the existing `BookStatus` enum, the status CHECK constraint in SQL, and the state machine transitions. Since embedding is a post-ingestion enrichment step (not a separate lifecycle), it's simpler to track it via the nullable `embedding_provider` field: None = not embedded, non-None = embedded.

**Alternatives considered:**

- Add `EMBEDDING` status: invasive change across schema, domain model, and existing code — overkill for v1
- Separate `is_embedded` boolean: adds a field when `embedding_provider is not None` already signals the same thing

### 8. EmbeddingVector domain value object

**Decision:** Define an `EmbeddingVector` frozen dataclass with `chunk_id: str` and `vector: list[float]`. This is what the use case passes to the repository.

**Rationale:** Gives a typed container for the chunk-to-vector mapping. Without it, the use case would pass parallel lists or tuples, which is error-prone. Being a domain value object, it carries no behavior — just data with validation (non-empty vector, vector length matches expected dimension).

## Risks / Trade-offs

**[Risk] OpenAI API rate limits or failures during batch embedding** → Mitigation: For v1, a failure during embedding is not catastrophic — the book remains READY but without embeddings. The user can retry. Incremental embedding (Phase 7) will handle resume-from-failure.

**[Risk] sqlite-vec may not be available on all platforms** → Mitigation: sqlite-vec is a loadable extension. The Python CLI loads it explicitly. The Swift app will need a separate solution (Phase 8). For now, Python-only scope.

**[Risk] Per-provider tables grow large with many books** → Mitigation: sqlite-vec handles this well. Standard indexes on `book_id` keep per-book queries fast. Far better than per-book tables which would create hundreds of tables.

**[Trade-off] No incremental embedding** → If embedding fails midway, all progress is lost. Acceptable for v1 (typical books embed in 1-2 API calls). Phase 7 can add resume support.

**[Trade-off] Only OpenAI provider** → Users need an OpenAI API key even if they use Anthropic for chat. Acceptable per the technical design ("start with easiest first"). Ollama and Apple NaturalLanguage providers come later.
