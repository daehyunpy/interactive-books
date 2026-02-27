## 1. Tool definitions — page tool

- [x] 1.1 Add `SET_PAGE_TOOL` constant in `app/chat.py` — name `"set_page"`, required `page` (integer) parameter

> Design evolution: `get_current_page` was dropped — the LLM can infer the page from conversation context, and `set_page` with page 0 resets. `set_current_page` was renamed to `set_page` for brevity.

## 2. Application — ChatWithBookUseCase

- [x] 2.1 Add `book_repo: BookRepository` to constructor
- [x] 2.2 Define `set_page_handler` closure: parses page, calls `book.set_current_page(page)`, persists via `book_repo.save()`, returns `ToolResult`
- [x] 2.3 Register both handlers in `tool_handlers` dict and pass both `ToolDefinition`s to `retrieval.execute()`

## 3. Infra — guard ToolResultEvent emission

- [x] 3.1 In `tool_use.py`, only emit `ToolResultEvent` when the filtered `search_results` list is non-empty (skip for page tools that return empty `results`)

## 4. System prompt — conversation_system_prompt.md

- [x] 4.1 Add `set_page` tool description to the prompt
- [x] 4.2 Add rule: use `set_page` when the reader mentions their page position

## 5. CLI wiring — main.py

- [x] 5.1 Pass `book_repo` to `ChatWithBookUseCase` constructor in the `chat` command

## 6. Tests — page tool handlers

- [x] 6.1 Test `set_page` handler updates and persists the page, returns `ToolResult`
- [x] 6.2 Test `set_page` with invalid page (negative) returns domain error in `ToolResult`
- [x] 6.3 Test `set_page` with non-numeric input returns error in `ToolResult`
- [x] 6.4 Test `set_page` with missing book returns error in `ToolResult`
- [x] 6.5 Test coercion: float → int and string → int (LLMs send 50.0 for integer params)
- [x] 6.6 Test both tools are passed to the retrieval strategy

## 7. Tests — ToolResultEvent guard

- [x] 7.1 Test `ToolUseRetrievalStrategy` does NOT emit `ToolResultEvent` when handler returns `ToolResult` with empty `results`
- [x] 7.2 Test `ToolUseRetrievalStrategy` still emits `ToolResultEvent` for search results (existing behavior preserved)

## 8. Tests — existing behavior preserved

- [x] 8.1 Verify existing chat tests still pass after adding `book_repo` parameter
- [x] 8.2 Run full test suite (`uv run pytest -x`)
- [x] 8.3 Run lint and type checks (`uv run ruff check .` and `uv run pyright`)
