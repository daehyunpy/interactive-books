## 1. Application Layer — SearchBooksUseCase

- [x] 1.1 Add `page_override: int | None = None` parameter to `SearchBooksUseCase.execute()`
- [x] 1.2 Compute `effective_page` from `page_override` (if not None) or `book.current_page`
- [x] 1.3 Replace `book.current_page` usage with `effective_page` for filtering and over-fetch decisions

## 2. Tests — page_override behavior

- [x] 2.1 Test `page_override` takes precedence over `book.current_page`
- [x] 2.2 Test `page_override=0` disables filtering even when `book.current_page > 0`
- [x] 2.3 Test `page_override=None` falls back to `book.current_page` (existing behavior preserved)
- [x] 2.4 Test over-fetching activates when `page_override` enables filtering

## 3. CLI — search command

- [x] 3.1 Add `--page` / `-p` option to `search` command in `main.py` (type `int | None`, default `None`)
- [x] 3.2 Pass `page_override=page` to `use_case.execute()`

## 4. CLI — `--all-pages` alias

- [x] 4.1 Add `--all-pages` boolean flag to `search` command, mutually exclusive with `--page`
- [x] 4.2 When `--all-pages` is set, pass `page_override=0` to `use_case.execute()`
- [x] 4.3 Raise error if both `--page` and `--all-pages` are provided

## 5. Verification

- [x] 5.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [x] 5.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
