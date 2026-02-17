## 1. Domain Layer

- [ ] 1.1 Create `BookSummary` frozen dataclass in `domain/book_summary.py` with `id`, `title`, `status`, `chunk_count`, `embedding_provider`, `current_page`
- [ ] 1.2 Write tests for `BookSummary` (creation, immutability)
- [ ] 1.3 Add `count_by_book(book_id: str) -> int` to `ChunkRepository` protocol in `domain/protocols.py`
- [ ] 1.4 Implement `count_by_book` in `infra/storage/chunk_repo.py` (`SELECT COUNT(*)`) and write integration test

## 2. Application Layer — New Use Cases

- [ ] 2.1 Create `ListBooksUseCase` in `app/list_books.py` that uses `chunk_repo.count_by_book()` to build `list[BookSummary]`
- [ ] 2.2 Write tests for `ListBooksUseCase` (books exist, empty list)
- [ ] 2.3 Create `DeleteBookUseCase` in `app/delete_book.py` that accepts `BookRepository` + `EmbeddingRepository` (not ChunkRepository — chunks cascade via FK). Fetches book first to get `embedding_provider`/`embedding_dimension`, deletes embeddings from vec0 table only if both are non-None, then deletes book.
- [ ] 2.4 Write tests for `DeleteBookUseCase` (book with embeddings, book without embeddings, not found)

## 3. CLI Helpers

- [ ] 3.1 Extract `_open_db(enable_vec=False)` helper in `main.py`
- [ ] 3.2 Extract `_require_env(name)` helper in `main.py`
- [ ] 3.3 Add `--verbose` flag to `@app.callback()` with module-level `_verbose` variable
- [ ] 3.4 Refactor existing commands (`ingest`, `embed`, `search`, `ask`) to use `_open_db` and `_require_env`

## 4. CLI — New Commands

- [ ] 4.1 Add `books` command — list all books in a formatted table
- [ ] 4.2 Add `show <book-id>` command — detailed single-book view
- [ ] 4.3 Add `delete <book-id>` command with `--yes` flag and `typer.confirm()` — compose with `BookRepository` + `EmbeddingRepository` (needs `enable_vec=True` for DB)
- [ ] 4.4 Add `set-page <book-id> <page>` command

## 5. Verbose Output

- [ ] 5.1 Add verbose output to `ask` command (model name, chunk count, timing)
- [ ] 5.2 Add verbose output to `search` command (provider, dimension, timing)

## 6. Verification

- [ ] 6.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 6.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
