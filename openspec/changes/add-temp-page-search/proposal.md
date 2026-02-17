## Why

The `search` command currently filters results based on `book.current_page`, which is a persisted value set via `set-page`. Users who want to try a one-off page-filtered search must first `set-page`, run the search, then `set-page 0` to reset — three commands for what should be one. A `--page` flag on the `search` command lets users do temporary page-filtered searches without touching the persisted state.

## What Changes

- Add `page_override: int | None` parameter to `SearchBooksUseCase.execute()`
- When `page_override` is provided, use it instead of `book.current_page` for filtering
- Add `--page` / `-p` CLI option to the `search` command
- Pass the CLI option through to the use case

## Capabilities

### Modified Capabilities

- `search-pipeline`: Add `page_override` parameter to `SearchBooksUseCase.execute()`
- `cli-commands`: Add `--page` / `-p` option to the `search` CLI command

## Impact

- **No new files**: All changes are in existing files
- **No new dependencies**: Uses existing infrastructure
- **No DB changes**: The override is transient — never persisted
- **Backward compatible**: `page_override=None` preserves all existing behavior
- **Scope**: `search` command only — `chat` command is out of scope
