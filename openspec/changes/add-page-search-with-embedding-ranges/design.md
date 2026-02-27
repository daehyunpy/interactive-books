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
- Consolidate `ChunkRepository.get_by_page()` and `get_up_to_page()` into a single `get_by_page_range(book_id, start_page, end_page)` method
- Refactor `RetrievalStrategy` to use a tool handler dispatch map instead of a single `search_fn` callback

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

**Decision:** Update `EmbeddingRepository.search()` to return `list[tuple[str, float, int, int]]` — `(chunk_id, distance, start_page, end_page)`. Update `SearchBooksUseCase` to use these page ranges directly for page info instead of deriving them from chunk lookup.

**Note:** The chunk lookup in `SearchBooksUseCase` remains necessary for `content` (which is not stored in the embedding table). The improvement is that **page ranges** come from embeddings, not that chunk lookup is eliminated entirely.

**Rationale:** Avoids the chunk-to-page-range lookup step in search. The page data comes directly from the embedding table. Content still requires the chunk table.

### 4. Page-range content retrieval (consolidated)

**Decision:** Replace `ChunkRepository.get_by_page(book_id, page)` and `get_up_to_page(book_id, page)` with a single `get_by_page_range(book_id: str, start_page: int, end_page: int) -> list[Chunk]`. Returns all chunks overlapping the range `[start_page, end_page]` using `WHERE start_page <= end_page_param AND end_page >= start_page_param`. Add a `search-page <book_id> <page>` CLI command that calls `get_by_page_range(book_id, page, page)`.

The previous two methods are subsumed:

- `get_by_page(book_id, page)` → `get_by_page_range(book_id, page, page)`
- `get_up_to_page(book_id, page)` → `get_by_page_range(book_id, 1, page)`

**Rationale:** Three methods with overlapping semantics are really one operation with different default arguments. Collapsing into one method simplifies the protocol (one implementation, one test path) and eliminates the risk of inconsistent behavior between methods. Since no users exist yet, there's no backwards-compatibility concern.

**Alternatives considered:**

- Keep all three methods: redundant protocol surface, more test doubles to maintain
- Use vector search with page filter: overkill for "show me page N" — no query needed
- Add to existing `search` command: conflates two different operations (semantic search vs page lookup)

### 5. RetrievalStrategy tool dispatch map

**Decision:** Replace the single `search_fn: Callable[[str], list[SearchResult]]` parameter on `RetrievalStrategy.execute()` with a generic dispatch map:

```python
tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]]
```

Each handler takes the tool's `arguments` dict and returns a `ToolResult` dataclass containing both the formatted text and event metadata (query, result count, raw results). The strategy dispatches by tool name: `handler = tool_handlers[invocation.tool_name]`. This preserves the ability to emit rich `ToolResultEvent` events.

**Rationale:** The current design hardcodes a single tool callback and blindly calls `search_fn(query)` for every invocation, ignoring `invocation.tool_name`. This breaks the moment a second tool (`read_pages`) is added with different argument shapes. A dispatch map:

- Separates routing from execution — each handler knows its own argument extraction
- Scales to N tools without protocol changes
- Makes each handler independently testable

The `AlwaysRetrieveStrategy` (Ollama fallback) doesn't use tool dispatch at all — it reformulates and always searches. The caller (`ChatWithBookUseCase`) extracts a `search_fn` from `tool_handlers["search_book"]` and passes it separately to `AlwaysRetrieveStrategy`, which keeps its current simple interface. This way, `AlwaysRetrieveStrategy` never sees the dispatch map.

**Unknown tool names:** If the LLM hallucinates a tool name not in the dispatch map, return an error string as the tool result (e.g., `"Unknown tool: {name}"`). This allows the LLM to self-correct in the next iteration rather than crashing the conversation turn.

**Alternatives considered:**

- Separate named parameters (`search_fn`, `read_pages_fn`): doesn't scale — every new tool changes the protocol signature
- Single polymorphic callback with tool name: possible, but the dispatch map is more explicit and testable

### 6. EmbedBookUseCase modification

**Decision:** Modify `EmbedBookUseCase` to populate `start_page` and `end_page` on `EmbeddingVector` by looking up the corresponding chunk's page ranges before embedding.

**Rationale:** The embed pipeline already loads chunks to get their content. Adding page range extraction is trivial.

## Risks / Trade-offs

**[Trade-off] Schema change requires re-embedding** - Existing books won't have page ranges in their embeddings until re-embedded. Since this is a pre-release app with no real users, there is no fallback for old data — users must re-run `embed` to rebuild the table with page range columns. No fallback code is needed.

**[Trade-off] sqlite-vec auxiliary column limitations** - sqlite-vec doesn't support WHERE clauses on auxiliary columns in MATCH queries. Page filtering still happens in Python after the vector search returns. The benefit is eliminating the chunk table lookup, not SQL-level filtering.
