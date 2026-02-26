## 1. Domain — ToolHandler type alias

- [ ] 1.1 Add `ToolHandler = Callable[[dict[str, object]], str]` type alias to `domain/protocols.py`
- [ ] 1.2 Update `RetrievalStrategy` protocol: replace `search_fn: Callable[[str], list[SearchResult]]` with `tool_handlers: dict[str, ToolHandler]`

## 2. Tool definitions — page tools

- [ ] 2.1 Add `GET_CURRENT_PAGE_TOOL` constant in `app/chat.py` — name `"get_current_page"`, no required parameters
- [ ] 2.2 Add `SET_CURRENT_PAGE_TOOL` constant in `app/chat.py` — name `"set_current_page"`, required `page` (integer) parameter

## 3. Infra — ToolUseRetrievalStrategy

- [ ] 3.1 Update `tool_use.py` `execute()` signature: `search_fn` → `tool_handlers`
- [ ] 3.2 Replace hardcoded search dispatch with generic handler lookup: `handler = tool_handlers[invocation.tool_name]` → `result = handler(invocation.arguments)`
- [ ] 3.3 Remove `_format_results()` from strategy (formatting moves to the search handler)
- [ ] 3.4 Remove `ToolResultEvent` emission from strategy (moves to the search handler)

## 4. Infra — AlwaysRetrieveStrategy

- [ ] 4.1 Update `always_retrieve.py` `execute()` signature: `search_fn` → `tool_handlers`
- [ ] 4.2 Extract search handler from `tool_handlers["search_book"]` and call with `{"query": query}`
- [ ] 4.3 Remove `_format_context()` and `ToolResultEvent` emission (handled by search handler)

## 5. Application — ChatWithBookUseCase

- [ ] 5.1 Add `book_repo: BookRepository` to constructor
- [ ] 5.2 Define `search_handler` closure: calls `SearchBooksUseCase.execute()`, formats results, emits `ToolResultEvent` via `on_event`
- [ ] 5.3 Define `get_page_handler` closure: reads `book.current_page` from `book_repo`
- [ ] 5.4 Define `set_page_handler` closure: calls `book.set_current_page(page)`, persists via `book_repo.save()`
- [ ] 5.5 Build `tool_handlers` dict and pass all three `ToolDefinition`s + handlers to `retrieval.execute()`

## 6. System prompt — conversation_system_prompt.md

- [ ] 6.1 Add `get_current_page` and `set_current_page` tool descriptions to the prompt
- [ ] 6.2 Add rule: use `set_current_page` when the reader mentions their page position

## 7. CLI wiring — main.py

- [ ] 7.1 Pass `book_repo` to `ChatWithBookUseCase` constructor in the `chat` command

## 8. Tests — tool handler dispatch

- [ ] 8.1 Test `ToolUseRetrievalStrategy` dispatches to correct handler by tool name
- [ ] 8.2 Test unknown tool name returns error message (graceful fallback)
- [ ] 8.3 Test `AlwaysRetrieveStrategy` calls search handler from `tool_handlers`

## 9. Tests — page tool handlers

- [ ] 9.1 Test `get_current_page` handler returns the book's current page as string
- [ ] 9.2 Test `set_current_page` handler updates and persists the page
- [ ] 9.3 Test `set_current_page` with invalid page (negative) raises domain error
- [ ] 9.4 Test all three tools are passed to the retrieval strategy

## 10. Tests — existing behavior preserved

- [ ] 10.1 Verify existing chat tests still pass after `search_fn` → `tool_handlers` migration
- [ ] 10.2 Run full test suite (`uv run pytest -x`)
- [ ] 10.3 Run lint and type checks (`uv run ruff check .` and `uv run pyright`)
