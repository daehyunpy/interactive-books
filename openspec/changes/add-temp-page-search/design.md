## Context

The `SearchBooksUseCase.execute()` method reads `book.current_page` to decide whether to filter results by page. When `current_page > 0`, chunks with `start_page > current_page` are excluded and the vector search over-fetches by 3x to compensate. The `current_page` value is persisted via `set-page` and stored in the database.

Users who want a one-off page-filtered search must mutate persistent state (set-page → search → set-page 0). A `page_override` parameter lets the use case accept a transient page value that takes precedence over the persisted one.

## Goals / Non-Goals

**Goals:**

- Add `page_override: int | None` parameter to `SearchBooksUseCase.execute()`
- When set, use `page_override` instead of `book.current_page` for filtering decisions
- Add `--page` / `-p` CLI option to the `search` command
- Preserve all existing behavior when `page_override` is not provided

**Non-Goals:**

- Adding `--page` to the `chat` command — out of scope
- Changing the `set-page` command or persisted `current_page` behavior
- Adding page validation against book's actual page count

## Decisions

### 1. `page_override` parameter on `execute()`

**Decision:** Add `page_override: int | None = None` as a keyword argument to `SearchBooksUseCase.execute()`. When `page_override is not None`, use it as the effective page for filtering. When `None`, fall back to `book.current_page` (existing behavior).

**Rationale:** This is the minimal change to support temporary overrides. The parameter is optional with a `None` default, so all existing callers (including `ChatWithBookUseCase`) continue working without modification. The `None` vs `0` distinction is intentional: `None` means "use the persisted value", `0` means "explicitly disable filtering".

**Alternatives considered:**

- Add a `page` field to a search options object: over-engineering for a single parameter
- Temporarily mutate `book.current_page` in memory: fragile, risks accidental persistence
- Add a separate `search_with_page()` method: duplicates logic

### 2. Effective page resolution

**Decision:** Compute `effective_page` at the top of the method:

```python
effective_page = page_override if page_override is not None else book.current_page
page_filtering = effective_page > 0
```

Then use `effective_page` everywhere `book.current_page` was used.

**Rationale:** Single point of resolution, clear precedence. The rest of the method logic (over-fetching, chunk filtering) remains unchanged — it just uses `effective_page` instead of `book.current_page`.

### 3. CLI option naming

**Decision:** `--page` / `-p` as a Typer `Option` with `default=None`, type `int | None`.

**Rationale:** Matches the existing `--top-k` / `-k` pattern. `None` default means the flag is truly optional — omitting it preserves existing behavior. `-p` is the natural short form.

## Risks / Trade-offs

**[Trade-off] No validation against book's actual page count** → A user can pass `--page 99999` on a 200-page book. This is consistent with `set-page` which also allows any non-negative value. Validation would require knowing the book's total pages, which isn't reliably tracked for all formats.
