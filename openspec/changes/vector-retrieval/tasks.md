## 1. Domain Layer

- [ ] 1.1 Create `SearchResult` frozen dataclass in `domain/search_result.py` with fields: `chunk_id`, `content`, `start_page`, `end_page`, `distance`
- [ ] 1.2 Add `search` method to `EmbeddingRepository` protocol in `domain/protocols.py`: `search(provider_name, dimension, book_id, query_vector, top_k) → list[tuple[str, float]]`

## 2. Infrastructure — sqlite-vec Search Adapter

- [ ] 2.1 Implement `search` method in `infra/storage/embedding_repo.py` using sqlite-vec `WHERE vector MATCH ? AND k = ? AND book_id = ?`
- [ ] 2.2 Write integration tests for `search`: returns nearest chunks, empty results for no embeddings, respects book_id partition, results include chunk_id and distance

## 3. Application Layer — SearchBooksUseCase

- [ ] 3.1 Create `SearchBooksUseCase` in `app/search.py` with constructor injection of `EmbeddingProvider`, `BookRepository`, `ChunkRepository`, `EmbeddingRepository`
- [ ] 3.2 Implement `execute(book_id, query, top_k=5)`: embed query, KNN search, join chunk metadata, return `list[SearchResult]`
- [ ] 3.3 Add book validation: raise `NOT_FOUND` if book doesn't exist, raise `INVALID_STATE` if book has no embeddings
- [ ] 3.4 Add page filtering: when `book.current_page > 0`, filter to chunks with `start_page <= current_page`; over-fetch `top_k * 3` to compensate
- [ ] 3.5 Write unit tests for use case: successful search, book not found, no embeddings, top_k limit, page filtering active/inactive, over-fetch behavior

## 4. CLI — Search Command

- [ ] 4.1 Wire `search <book-id> <query>` command in `main.py` with `--top-k` option (default 5)
- [ ] 4.2 Print result format: page range, distance score, content preview for each result; handle no-results and error cases

## 5. Verification

- [ ] 5.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 5.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
