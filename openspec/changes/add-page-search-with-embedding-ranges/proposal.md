## Why

Currently, page-range filtering in search happens as a post-filter: the embedding table returns the top-K nearest vectors, then `SearchBooksUseCase` filters out chunks beyond the reader's page. This wastes vector search budget on results that get discarded. Additionally, there's no way to retrieve all content for a specific page — users can only do semantic (query-based) search.

Storing `start_page` and `end_page` directly in the embedding table enables page-range filtering at the vector search level and supports a new "search by page" feature that returns all chunks overlapping a given page or page range.

## What Changes

- Extend the sqlite-vec virtual table schema to include `start_page` and `end_page` auxiliary columns
- Modify `EmbeddingRepository` to save and query page ranges with embeddings
- Consolidate `ChunkRepository.get_by_page()` and `get_up_to_page()` into a single `get_by_page_range(book_id, start_page, end_page)` method
- Add a `search-page <book_id> <page>` CLI command for page-based content retrieval
- Modify `SearchBooksUseCase` to leverage embedding-level page filtering when available
- Refactor `RetrievalStrategy` to use a `tool_handlers` dispatch map instead of a single `search_fn` callback, enabling multiple tool support (e.g., `search_book` + future `read_pages`)

## Capabilities

### New Capabilities

- `page-search`: Retrieve all chunks overlapping a specific page or page range

### Modified Capabilities

- `embedding-storage`: Store `start_page` and `end_page` as auxiliary columns in the embedding virtual table
- `search-pipeline`: Use embedding-level page metadata for more efficient filtering
- `cli-commands`: Add `search-page` command for page-based content retrieval

## Impact

- **New files**: None (modifications to existing files)
- **Modified files**: `infra/storage/embedding_repo.py` (schema + queries), `domain/protocols.py` (updated protocol — `ChunkRepository`, `RetrievalStrategy`), `domain/embedding_vector.py` (add page fields), `app/search.py` (efficiency improvement), `app/chat.py` (dispatch map wiring), `infra/retrieval/tool_use.py` (dispatch logic), `infra/retrieval/always_retrieve.py` (signature update), `main.py` (new CLI command)
- **DB migration**: New virtual table schema version with auxiliary columns (backward-compatible — creates new table alongside old)
- **Backward compatible**: Old embeddings without page ranges still work; re-embed to populate page data
