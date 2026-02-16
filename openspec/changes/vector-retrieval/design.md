## Context

Phase 4 built the embedding pipeline: chunks are embedded via OpenAI and stored in per-provider sqlite-vec virtual tables (`embeddings_openai_1536`). The table uses `book_id` as a partition key and `chunk_id` as an auxiliary column. The `chunks` table stores the text content, page ranges, and chunk index. Phase 5 connects these by adding KNN vector search — the retrieval step in the RAG pipeline.

The technical design specifies: vector search with page filtering (no spoilers), top-k configurable (default 5), and a `cli search` command.

## Goals / Non-Goals

**Goals:**

- Add a `SearchResult` domain value object carrying chunk reference, distance score, and page info
- Extend `EmbeddingRepository` protocol with a `search` method for KNN vector search
- Implement KNN search in the sqlite-vec adapter with book_id partition filtering and page-range join
- Build a `SearchBooksUseCase` that embeds the query, searches, and returns page-filtered results
- Wire a `cli search <book-id> <query>` command for testing
- Support `current_page` filtering: when set (> 0), only return chunks where `start_page <= current_page`

**Non-Goals:**

- Q&A / LLM answering — that is Phase 6
- Multi-book search — search is per-book for now
- Hybrid search (keyword + vector) — pure vector search for v1
- Re-ranking — return raw KNN results, no secondary re-ranker
- Search result caching — not needed at this scale

## Decisions

### 1. SearchResult value object

**Decision:** Define a `SearchResult` frozen dataclass with `chunk_id: str`, `content: str`, `start_page: int`, `end_page: int`, `distance: float`. This is what the use case returns to callers.

**Rationale:** The caller needs chunk content, page location, and similarity score. Returning full `Chunk` objects would work but the caller doesn't need `book_id` or `chunk_index`. A dedicated value object keeps the search API focused. The `distance` field uses sqlite-vec's L2 distance (lower = more similar).

**Alternatives considered:**

- Return `list[Chunk]` with distance as a separate list: parallel lists are error-prone
- Return `list[tuple[Chunk, float]]`: works but unnamed fields are less readable
- Add distance to Chunk: mutates an existing domain object for a search-specific concern

### 2. Extend EmbeddingRepository with search method

**Decision:** Add `search(provider_name, dimension, book_id, query_vector, top_k) → list[tuple[str, float]]` to the `EmbeddingRepository` protocol. Returns `(chunk_id, distance)` pairs. The use case joins chunk_ids against the chunks table to build `SearchResult` objects.

**Rationale:** The repository is responsible for vector storage and retrieval. Search is the read side of that contract. Returning only `(chunk_id, distance)` keeps the repository focused on the vector layer — it doesn't need to know about chunk content or pages. The use case handles the join, which keeps the domain logic (page filtering) in the application layer.

**Alternatives considered:**

- New `SearchRepository` protocol: unnecessary abstraction for a single method on an existing contract
- Repository does the chunk join: mixes vector search with relational queries, violates single responsibility
- Repository returns full SearchResult: requires access to chunk content, which belongs to ChunkRepository

### 3. sqlite-vec KNN with partition key pre-filtering

**Decision:** The KNN query uses `WHERE vector MATCH ? AND k = ? AND book_id = ?` to leverage sqlite-vec's partition key optimization. This scopes the search to a single book's vectors.

**Rationale:** Our table schema already defines `book_id text partition key`. sqlite-vec recognizes partition key constraints and pre-filters before the KNN scan, making per-book searches efficient even with many books in one table.

### 4. Page filtering in the use case, not the repository

**Decision:** The repository returns raw KNN results (top_k chunk_ids + distances). The use case fetches chunk metadata from `ChunkRepository`, filters by `start_page <= current_page` (when current_page > 0), and assembles `SearchResult` objects.

**Rationale:** Page filtering is domain logic — it depends on reading position, which is a domain concept. The vector table doesn't store page ranges (those are in the `chunks` table). Doing the filter in the use case keeps the repository a pure vector search layer. We over-fetch from the vector layer (request more than top_k) to compensate for post-filtering.

**Alternatives considered:**

- SQL JOIN in the repository query: couples vector search to chunk schema, hard to test
- Store page ranges in the vector table as metadata columns: duplicates data, complicates inserts/updates

### 5. Over-fetch to compensate for page filtering

**Decision:** When `current_page > 0`, the use case requests `top_k * 3` results from the vector search, then filters by page, then trims to `top_k`. This ensures enough results survive the page filter.

**Rationale:** If a book has 200 chunks and the user is on page 50, roughly half the chunks may be beyond the current page. Fetching 3x ensures we almost always get at least `top_k` results after filtering. The multiplier is a reasonable heuristic — not so large that it's wasteful, not so small that results are sparse.

**Alternatives considered:**

- Fetch all vectors for the book: wasteful for large books
- Exact calculation based on page distribution: complex, premature optimization
- Fixed large number (e.g., 100): less adaptive

### 6. Query embedding uses the same provider

**Decision:** The `SearchBooksUseCase` embeds the query text using the same `EmbeddingProvider` that was used to embed the book's chunks. It reads `book.embedding_provider` and `book.embedding_dimension` to determine the table.

**Rationale:** Vector similarity only works when query and document vectors are from the same model and dimension. The book already stores which provider/dimension was used.

## Risks / Trade-offs

**[Risk] Page filtering removes too many results** → Mitigation: Over-fetch by 3x. If still not enough, return what we have (partial results are better than none). Phase 7 polish can add smarter strategies.

**[Risk] Large books have slow KNN queries** → Mitigation: sqlite-vec partition key pre-filtering limits the scan to one book's vectors. For a 1000-page book with ~500 chunks, this is a small index. Not a concern for v1.

**[Trade-off] Two-step search (vector search + chunk lookup)** → Requires two queries instead of one JOIN. But this keeps the repository boundaries clean and is negligible at our scale (< 1000 chunks per book).

**[Trade-off] Over-fetching wastes some computation** → Fetching 3x top_k from the vector index is cheap (sqlite-vec returns results in microseconds). The cost is negligible vs. the API call to embed the query.
