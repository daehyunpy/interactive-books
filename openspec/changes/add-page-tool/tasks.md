## 1. Tool definitions — page tools

- [ ] 1.1 Add `GET_CURRENT_PAGE_TOOL` constant in `app/chat.py` — name `"get_current_page"`, no required parameters
- [ ] 1.2 Add `SET_CURRENT_PAGE_TOOL` constant in `app/chat.py` — name `"set_current_page"`, required `page` (integer) parameter

## 2. Application — ChatWithBookUseCase

- [ ] 2.1 Add `book_repo: BookRepository` to constructor
- [ ] 2.2 Define `get_page_handler` closure: reads `book.current_page` from `book_repo`, returns `ToolResult(formatted_text=..., query="", result_count=0)`
- [ ] 2.3 Define `set_page_handler` closure: calls `book.set_current_page(page)`, persists via `book_repo.save()`, returns `ToolResult`
- [ ] 2.4 Register all three handlers in `tool_handlers` dict and pass all three `ToolDefinition`s to `retrieval.execute()`

## 3. Infra — guard ToolResultEvent emission

- [ ] 3.1 In `tool_use.py`, only emit `ToolResultEvent` when the filtered `search_results` list is non-empty (skip for page tools that return empty `results`)

## 4. System prompt — conversation_system_prompt.md

- [ ] 4.1 Add `get_current_page` and `set_current_page` tool descriptions to the prompt
- [ ] 4.2 Add rule: use `set_current_page` when the reader mentions their page position

## 5. CLI wiring — main.py

- [ ] 5.1 Pass `book_repo` to `ChatWithBookUseCase` constructor in the `chat` command

## 6. Tests — page tool handlers

- [ ] 6.1 Test `get_current_page` handler returns the book's current page as formatted string in `ToolResult`
- [ ] 6.2 Test `set_current_page` handler updates and persists the page, returns `ToolResult`
- [ ] 6.3 Test `set_current_page` with invalid page (negative) raises domain error
- [ ] 6.4 Test all three tools are passed to the retrieval strategy

## 7. Tests — ToolResultEvent guard

- [ ] 7.1 Test `ToolUseRetrievalStrategy` does NOT emit `ToolResultEvent` when handler returns `ToolResult` with empty `results`
- [ ] 7.2 Test `ToolUseRetrievalStrategy` still emits `ToolResultEvent` for search results (existing behavior preserved)

## 8. Tests — existing behavior preserved

- [ ] 8.1 Verify existing chat tests still pass after adding `book_repo` parameter
- [ ] 8.2 Run full test suite (`uv run pytest -x`)
- [ ] 8.3 Run lint and type checks (`uv run ruff check .` and `uv run pyright`)
