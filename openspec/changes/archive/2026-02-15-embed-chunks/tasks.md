## 1. Domain Layer

- [x] 1.1 Add `EMBEDDING_FAILED` to `BookErrorCode` enum in `domain/errors.py`
- [x] 1.2 Add `EmbeddingVector` frozen dataclass to `domain/embedding_vector.py` (chunk_id: str, vector: list[float], validates non-empty vector) with tests
- [x] 1.3 Add `EmbeddingProvider` protocol to `domain/protocols.py` with `embed(texts: list[str]) → list[list[float]]`, `provider_name: str`, `dimension: int`
- [x] 1.4 Add `EmbeddingRepository` protocol to `domain/protocols.py` with `ensure_table(provider_name, dimension)`, `save_embeddings(provider_name, dimension, embeddings)`, `delete_by_book(provider_name, dimension, book_id)`, `has_embeddings(book_id, provider_name, dimension)`

## 2. Schema Migration

- [x] 2.1 Create `shared/schema/002_add_embeddings.sql` that loads the sqlite-vec extension
- [x] 2.2 Update `Database` to load the sqlite-vec extension when running migrations

## 3. OpenAI Embedding Adapter

- [x] 3.1 Add `openai` dependency to `pyproject.toml`
- [x] 3.2 Implement `EmbeddingProvider` adapter in `infra/embeddings/openai.py` using text-embedding-3-small (1536d), returning provider_name="openai" and dimension=1536
- [x] 3.3 Write tests for OpenAI adapter (batch embed, provider metadata, API key missing, API failure) using mocked HTTP responses

## 4. sqlite-vec Storage Adapter

- [x] 4.1 Add `sqlite-vec` dependency to `pyproject.toml`
- [x] 4.2 Implement `EmbeddingRepository` adapter in `infra/storage/embedding_repo.py` — ensure*table, save_embeddings, delete_by_book, has_embeddings using per-provider virtual tables named `embeddings*{provider}\_{dimension}`
- [x] 4.3 Write tests for sqlite-vec adapter (ensure table, ensure table idempotent, save embeddings, delete by book, has_embeddings true/false)

## 5. Embed Use Case

- [x] 5.1 Implement `EmbedBookUseCase` in `app/embed.py` — load book + chunks, batch embed (default 100), store vectors via repository, update book metadata (embedding_provider, embedding_dimension)
- [x] 5.2 Write tests for use case (successful embed, book not found, no chunks, re-embed deletes old embeddings, API failure cleans up and preserves book state)

## 6. CLI Command

- [x] 6.1 Wire `embed` command in `main.py` via Typer — accept book_id argument, print title/provider/dimension/vector count on success, print error on failure

## 7. Verification

- [x] 7.1 Run full test suite (`uv run pytest -x`), lint (`uv run ruff check .`), and type check (`uv run pyright`) — all passing
