## 1. Domain Layer — EmbeddingVector Page Ranges

- [x] 1.1 Add `start_page: int` and `end_page: int` fields to `EmbeddingVector` in `domain/embedding_vector.py`
  - Validation: start_page >= 1, end_page >= start_page
- [ ] 1.2 Update unit tests for `EmbeddingVector` with new fields

## 2. Domain Layer — ChunkRepository Protocol

- [ ] 2.1 Replace `get_by_page(book_id, page)` and `get_up_to_page(book_id, page)` with `get_by_page_range(book_id: str, start_page: int, end_page: int) -> list[Chunk]` in `domain/protocols.py`
  - Returns chunks where `start_page <= end_page_param AND end_page >= start_page_param`
  - Remove both old methods from the protocol

## 3. Domain Layer — EmbeddingRepository Protocol

- [x] 3.1 Update `save_embeddings` signature in `EmbeddingRepository` protocol to accept page ranges (already part of `EmbeddingVector`)
- [x] 3.2 Update `search` return type to `list[tuple[str, float, int, int]]` (chunk_id, distance, start_page, end_page)

## 4. Infrastructure — Embedding Storage

- [x] 4.1 Update `ensure_table()` in `infra/storage/embedding_repo.py` to include `+start_page INTEGER` and `+end_page INTEGER` auxiliary columns
- [x] 4.2 Update `save_embeddings()` to persist `start_page` and `end_page` from `EmbeddingVector`
- [x] 4.3 Update `search()` to return `start_page` and `end_page` from query results
- [ ] 4.4 Add/update integration tests for embedding repo with page ranges

## 5. Infrastructure — Chunk Storage

- [ ] 5.1 Replace `get_by_page()` and `get_up_to_page()` with `get_by_page_range(book_id, start_page, end_page)` in `infra/storage/chunk_repo.py`
  - SQL: `WHERE book_id = ? AND start_page <= ? AND end_page >= ? ORDER BY chunk_index`
- [ ] 5.2 Update/replace existing `get_by_page` and `get_up_to_page` tests with `get_by_page_range` tests
  - Test single-page range (equivalent to old `get_by_page`)
  - Test range from page 1 (equivalent to old `get_up_to_page`)
  - Test multi-page range
  - Test empty result for non-overlapping range
- [ ] 5.3 Update all callers: `main.py` `search-page` command, test doubles in `tests/app/`

## 6. Application Layer — EmbedBookUseCase

- [x] 6.1 Modify `EmbedBookUseCase` to populate `start_page` and `end_page` on `EmbeddingVector` from chunk data
- [ ] 6.2 Update embed tests to verify page ranges are propagated

## 7. Application Layer — SearchBooksUseCase

- [x] 7.1 Update `SearchBooksUseCase` to use page ranges from embedding search results for page info (chunk lookup remains for content)
- [ ] ~~7.2 Add fallback: if page ranges not available from embeddings (old data), fall back to chunk lookup~~ **Removed:** No fallback needed — pre-release app, users must re-embed to get page ranges.
- [ ] 7.3 Update search tests for new return format

## 8. Domain Layer — RetrievalStrategy Dispatch Map

- [ ] 8.1 Update `RetrievalStrategy` protocol in `domain/protocols.py`: replace `search_fn: Callable[[str], list[SearchResult]]` with `tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]]`
  - Create a `ToolResult` dataclass in `domain/tool.py` with `formatted_text: str` and event metadata (`query: str`, `result_count: int`, `results: list[SearchResult]`)
- [ ] 8.2 Update `infra/retrieval/tool_use.py` to dispatch by `invocation.tool_name` via the handler map
  - Look up handler: `handler = tool_handlers.get(invocation.tool_name)`
  - If unknown tool name: return error string `"Unknown tool: {name}"` as tool result (allows LLM to self-correct)
  - Call handler with arguments: `result = handler(dict(invocation.arguments))`
  - Use `ToolResult.formatted_text` for the LLM response, metadata for `ToolResultEvent` emission
- [ ] 8.3 Update `infra/retrieval/always_retrieve.py`: receives `search_fn` extracted by the caller (not the dispatch map directly)
  - `ChatWithBookUseCase` extracts `search_fn` from `tool_handlers["search_book"]` and passes it to `AlwaysRetrieveStrategy` separately
  - `AlwaysRetrieveStrategy` keeps its current simple `search_fn: Callable` interface
- [ ] 8.4 Update `app/chat.py` to build a `tool_handlers` dict and pass it to the strategy
  - `search_book` handler wraps `search_use_case.execute()`, formats results, and returns `ToolResult`
  - For `AlwaysRetrieveStrategy`: extract `search_fn` from the handler and pass it separately
- [ ] 8.5 Update all retrieval strategy tests and test doubles

## 9. CLI — `search-page` Command

- [x] 9.1 Add `search-page <book_id> <page>` command to `main.py` _(exists but uses old `get_by_page` — will be updated by task 5.3)_
  - Uses `chunk_repo.get_by_page_range(book_id, page, page)` for single-page lookup
  - Displays all chunks overlapping the given page, ordered by chunk_index
  - Shows chunk content with page range annotations
- [ ] 9.2 Add CLI test for `search-page` command

## 10. Testing Infrastructure

- [ ] 10.1 Create shared `tests/fakes.py` module consolidating `FakeChunkRepository` (and other common fakes) from `tests/app/test_search.py`, `test_embed.py`, `test_list_books.py`, `test_ingest.py`
  - Implement `get_by_page_range` on the shared fake
  - Update all four test files to import from `tests/fakes.py`

## 11. Verification

- [ ] 11.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 11.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
