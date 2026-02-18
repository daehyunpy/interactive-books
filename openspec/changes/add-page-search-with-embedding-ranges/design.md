## Context

The embedding repository uses sqlite-vec virtual tables with schema: `(book_id TEXT partition key, +chunk_id TEXT, vector float[N])`. The `search()` method returns `[(chunk_id, distance)]` pairs. Page filtering then happens in `SearchBooksUseCase` by looking up chunks and checking `start_page <= effective_page`. This means the vector search may return results that get discarded, wasting the top-K budget.

Separately, there's no CLI command to retrieve all content on a specific page — users can only do semantic search via the `search` command.

## Goals / Non-Goals

**Goals:**

- Store `start_page` and `end_page` as auxiliary columns in the sqlite-vec virtual table
- Modify `EmbeddingVector` to carry page range metadata
- Update `EmbeddingRepository.save_embeddings()` to persist page ranges
- Update `EmbeddingRepository.search()` to return page ranges alongside chunk_id and distance
- Add a `search-page <book_id> <page>` CLI command that retrieves all chunks overlapping the given page
- Add `ChunkRepository.get_by_page(book_id, page)` for direct page-based retrieval

**Non-Goals:**

- Migrating existing embedding tables (users re-embed to get page ranges)
- Changing the vector similarity algorithm
- Adding page-range filtering at the SQL level in vector search (sqlite-vec doesn't support WHERE on auxiliary columns in MATCH queries — post-filtering remains necessary for semantic search)

## Decisions

### 1. Auxiliary columns in sqlite-vec

**Decision:** Add `+start_page INTEGER` and `+end_page INTEGER` as auxiliary columns in the virtual table:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_{provider}_{dimension} USING vec0(
    book_id TEXT partition key,
    +chunk_id TEXT,
    +start_page INTEGER,
    +end_page INTEGER,
    vector float[{dimension}]
)
```

**Rationale:** sqlite-vec supports auxiliary columns (prefixed with `+`) that are stored alongside vectors but not used in similarity calculations. These columns are returned in query results, eliminating the need to join with the chunks table for page info. This is the idiomatic way to store metadata in sqlite-vec.

**Impact:** This changes the table schema. Since virtual tables can't be ALTERed, the new schema applies to newly created tables. Existing books need re-embedding to get the new columns.

### 2. EmbeddingVector page fields

**Decision:** Add `start_page: int` and `end_page: int` fields to `EmbeddingVector`:

```python
@dataclass(frozen=True)
class EmbeddingVector:
    chunk_id: str
    vector: list[float]
    start_page: int
    end_page: int
```

**Rationale:** The value object should carry all data that gets persisted with the embedding. Since chunks already have page ranges and are the source of embedding vectors, propagating page ranges through `EmbeddingVector` is natural.

### 3. Search result enrichment

**Decision:** Update `EmbeddingRepository.search()` to return `list[tuple[str, float, int, int]]` — `(chunk_id, distance, start_page, end_page)`. Update `SearchBooksUseCase` to use these page ranges directly instead of looking up chunks.

**Rationale:** Avoids the chunk lookup step in search, making the search path more efficient. The page data comes directly from the embedding table.

### 4. Page-based content retrieval

**Decision:** Add `ChunkRepository.get_by_page(book_id: str, page: int) -> list[Chunk]` that returns all chunks where `start_page <= page AND end_page >= page`. Add a `search-page <book_id> <page>` CLI command that calls this method and displays results.

**Rationale:** This is a simple, direct lookup — no embeddings or vector search needed. It answers "what's on page N?" efficiently using the existing `idx_chunks_book_page_range` index.

**Alternatives considered:**

- Use vector search with page filter: overkill for "show me page N" — no query needed
- Add to existing `search` command: conflates two different operations (semantic search vs page lookup)

### 5. EmbedBookUseCase modification

**Decision:** Modify `EmbedBookUseCase` to populate `start_page` and `end_page` on `EmbeddingVector` by looking up the corresponding chunk's page ranges before embedding.

**Rationale:** The embed pipeline already loads chunks to get their content. Adding page range extraction is trivial.

## Risks / Trade-offs

**[Trade-off] Schema change requires re-embedding** - Existing books won't have page ranges in their embeddings until re-embedded. The `search` command still works (falls back to chunk lookup for page info), but the efficiency gain only applies to newly embedded books.

**[Trade-off] sqlite-vec auxiliary column limitations** - sqlite-vec doesn't support WHERE clauses on auxiliary columns in MATCH queries. Page filtering still happens in Python after the vector search returns. The benefit is eliminating the chunk table lookup, not SQL-level filtering.
