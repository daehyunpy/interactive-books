## Why

Phases 1-6 built the full pipeline (ingest → embed → search → ask) but the CLI has gaps: no way to list books, no `delete` command, duplicated DB/API-key boilerplate in every command, and no `--verbose` flag for debugging. Phase 7 fills these gaps so the CLI is a complete, usable tool before moving to the iOS/macOS app in Phase 8.

## What Changes

- Add `books` command — list all books with status, chunk count, and embedding info
- Add `show <book-id>` command — detailed view of a single book
- Add `delete <book-id>` command — remove a book and all associated data
- Add `set-page <book-id> <page>` command — set current reading position for page-scoped retrieval
- Add `--verbose` global flag — show model names, timing, and operational details
- Extract shared DB setup and API-key validation into helpers to reduce command boilerplate
- Improve error formatting consistency across all commands

## Capabilities

### New Capabilities

- `cli-commands`: New CLI commands (`books`, `show`, `delete`, `set-page`) and their use cases
- `cli-helpers`: Shared CLI infrastructure (DB setup helper, API-key validation, verbose output)

### Modified Capabilities

- `ask-pipeline`: Add `--verbose` output to `ask` command (show model name, chunk count, timing)
- `search-pipeline`: Add `--verbose` output to `search` command (show provider, dimension, timing)

## Impact

- **Modified file**: `main.py` — add new commands, global `--verbose` flag, refactor shared setup
- **New files**: `app/list_books.py`, `app/delete_book.py` — new use cases
- **No new dependencies** — uses existing typer, domain models, and repos
- **No domain changes** — all needed domain operations (get_all, delete, set_current_page) already exist
- **Existing commands unchanged** in behavior — only add verbose output and refactor internals
