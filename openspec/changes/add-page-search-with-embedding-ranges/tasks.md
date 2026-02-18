## 1. Domain Layer — EmbeddingVector Page Ranges

- [ ] 1.1 Add `start_page: int` and `end_page: int` fields to `EmbeddingVector` in `domain/embedding_vector.py`
  - Validation: start_page >= 1, end_page >= start_page
- [ ] 1.2 Update unit tests for `EmbeddingVector` with new fields

## 2. Domain Layer — ChunkRepository Protocol

- [ ] 2.1 Add `get_by_page(book_id: str, page: int) -> list[Chunk]` to `ChunkRepository` protocol in `domain/protocols.py`

## 3. Domain Layer — EmbeddingRepository Protocol

- [ ] 3.1 Update `save_embeddings` signature in `EmbeddingRepository` protocol to accept page ranges (already part of `EmbeddingVector`)
- [ ] 3.2 Update `search` return type to `list[tuple[str, float, int, int]]` (chunk_id, distance, start_page, end_page)

## 4. Infrastructure — Embedding Storage

- [ ] 4.1 Update `ensure_table()` in `infra/storage/embedding_repo.py` to include `+start_page INTEGER` and `+end_page INTEGER` auxiliary columns
- [ ] 4.2 Update `save_embeddings()` to persist `start_page` and `end_page` from `EmbeddingVector`
- [ ] 4.3 Update `search()` to return `start_page` and `end_page` from query results
- [ ] 4.4 Add/update integration tests for embedding repo with page ranges

## 5. Infrastructure — Chunk Storage

- [ ] 5.1 Implement `get_by_page(book_id, page)` in `infra/storage/chunk_repo.py` using `WHERE start_page <= ? AND end_page >= ?`
- [ ] 5.2 Add tests for `get_by_page`

## 6. Application Layer — EmbedBookUseCase

- [ ] 6.1 Modify `EmbedBookUseCase` to populate `start_page` and `end_page` on `EmbeddingVector` from chunk data
- [ ] 6.2 Update embed tests to verify page ranges are propagated

## 7. Application Layer — SearchBooksUseCase

- [ ] 7.1 Update `SearchBooksUseCase` to use page ranges from embedding search results directly (skip chunk lookup for page info)
- [ ] 7.2 Add fallback: if page ranges not available from embeddings (old data), fall back to chunk lookup
- [ ] 7.3 Update search tests for new return format

## 8. CLI — `search-page` Command

- [ ] 8.1 Add `search-page <book_id> <page>` command to `main.py`
  - Displays all chunks overlapping the given page, ordered by chunk_index
  - Shows chunk content with page range annotations
- [ ] 8.2 Add CLI test for `search-page` command

## 9. Verification

- [ ] 9.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 9.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
