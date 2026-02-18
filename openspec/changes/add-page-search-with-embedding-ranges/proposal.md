## Why

Currently, page-range filtering in search happens as a post-filter: the embedding table returns the top-K nearest vectors, then `SearchBooksUseCase` filters out chunks beyond the reader's page. This wastes vector search budget on results that get discarded. Additionally, there's no way to retrieve all content for a specific page — users can only do semantic (query-based) search.

Storing `start_page` and `end_page` directly in the embedding table enables page-range filtering at the vector search level and supports a new "search by page" feature that returns all chunks overlapping a given page or page range.

## What Changes

- Extend the sqlite-vec virtual table schema to include `start_page` and `end_page` auxiliary columns
- Modify `EmbeddingRepository` to save and query page ranges with embeddings
- Add a `get_by_page` method to `ChunkRepository` for direct page-based chunk retrieval
- Add a `search-page <book_id> <page>` CLI command (or `--page-range` option) to retrieve content by page
- Modify `SearchBooksUseCase` to leverage embedding-level page filtering when available

## Capabilities

### New Capabilities

- `page-search`: Retrieve all chunks overlapping a specific page or page range

### Modified Capabilities

- `embedding-storage`: Store `start_page` and `end_page` as auxiliary columns in the embedding virtual table
- `search-pipeline`: Use embedding-level page metadata for more efficient filtering
- `cli-commands`: Add `search-page` command for page-based content retrieval

## Impact

- **New files**: None (modifications to existing files)
- **Modified files**: `infra/storage/embedding_repo.py` (schema + queries), `domain/protocols.py` (updated protocol), `domain/embedding_vector.py` (add page fields), `app/search.py` (efficiency improvement), `main.py` (new CLI command)
- **DB migration**: New virtual table schema version with auxiliary columns (backward-compatible — creates new table alongside old)
- **Backward compatible**: Old embeddings without page ranges still work; re-embed to populate page data
