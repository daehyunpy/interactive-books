## 1. Application Layer — SearchBooksUseCase

- [ ] 1.1 Add `page_override: int | None = None` parameter to `SearchBooksUseCase.execute()`
- [ ] 1.2 Compute `effective_page` from `page_override` (if not None) or `book.current_page`
- [ ] 1.3 Replace `book.current_page` usage with `effective_page` for filtering and over-fetch decisions

## 2. Tests — page_override behavior

- [ ] 2.1 Test `page_override` takes precedence over `book.current_page`
- [ ] 2.2 Test `page_override=0` disables filtering even when `book.current_page > 0`
- [ ] 2.3 Test `page_override=None` falls back to `book.current_page` (existing behavior preserved)
- [ ] 2.4 Test over-fetching activates when `page_override` enables filtering

## 3. CLI — search command

- [ ] 3.1 Add `--page` / `-p` option to `search` command in `main.py` (type `int | None`, default `None`)
- [ ] 3.2 Pass `page_override=page` to `use_case.execute()`

## 4. Verification

- [ ] 4.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 4.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
