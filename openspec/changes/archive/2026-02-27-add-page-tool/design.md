## Context

The agentic chat loop supports a `search_book` tool. The summarization merge (`186b0b5`) already generalized the `RetrievalStrategy` protocol from a `search_fn: Callable[[str], list[SearchResult]]` callback to a `tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]]` dispatch map. Both strategy implementations (`tool_use.py`, `always_retrieve.py`) and the search handler in `ChatWithBookUseCase` use this pattern.

The `Book` entity already has `current_page` with `set_current_page(page)` domain logic and validation. The `BookRepository` protocol already has `save()` and `get()`. No new domain concepts or DB changes are needed — this change wires existing domain capabilities into the chat tool system as additional handlers in the existing dispatch map.

### Current handler/event flow

```
ChatWithBookUseCase.execute()
│
├─ defines search_book_handler(args) -> ToolResult
│    └─ ToolResult(formatted_text=..., query=..., result_count=N, results=[SearchResult, ...])
│
└─ strategy.execute(..., tool_handlers={"search_book": handler})
     │
     ├─ handler = tool_handlers[invocation.tool_name]
     ├─ result = handler(args)
     ├─ uses result.formatted_text as tool_result content for LLM
     └─ emits ToolResultEvent(query=result.query, result_count=..., results=filtered SearchResults)
```

The `ToolResult` type has search-specific fields (`query`, `result_count`, `results`). For page tools, these fields would carry empty/zero values. The strategy must guard `ToolResultEvent` emission so page tool calls don't produce spurious search-specific events.

## Goals / Non-Goals

**Goals:**

- Add `get_current_page` tool: LLM can read the book's current page position
- Add `set_current_page` tool: LLM can update the page position when the user says where they are
- Add page tool handler closures in `ChatWithBookUseCase` that return `ToolResult`
- Give `ChatWithBookUseCase` access to `BookRepository` for page tool handlers
- Guard `ToolResultEvent` emission in `ToolUseRetrievalStrategy` to only fire for search results
- Update conversation system prompt to describe the new tools

**Non-Goals:**

- Adding a `read_page` tool that fetches raw page text (future work)
- Changing how `current_page` filters search results (existing behavior preserved)
- Adding new event types for page tools (existing `ToolInvocationEvent` is sufficient)
- Changing the `ToolResult` type or handler return signature (already established)

## Decisions

### 1. Page tool handlers return `ToolResult` (matching existing pattern)

**Decision:** Page tool handlers return `ToolResult` with `formatted_text` carrying the meaningful response and search-specific fields zeroed out:

```python
def get_page_handler(arguments: dict[str, object]) -> ToolResult:
    book = book_repo.get(book_id)
    return ToolResult(
        formatted_text=f"The reader's current page is {book.current_page}.",
        query="",
        result_count=0,
    )
```

**Rationale:** The `ToolResult` type and handler signature `Callable[[dict[str, object]], ToolResult]` are already established across the protocol, both strategies, and the search handler. Adding a second return type (e.g., `str`) would require a `Union` return, protocol changes, and conditional logic in the strategy. Using `ToolResult` with empty search fields is simpler and keeps the dispatch generic.

**Trade-off:** `ToolResult.query` and `ToolResult.result_count` are meaningless for page tools. This is acceptable because (a) the strategy only uses `formatted_text` to build the LLM response, and (b) we guard `ToolResultEvent` emission to skip non-search results.

### 2. Guard `ToolResultEvent` emission for non-search tools

**Decision:** In `ToolUseRetrievalStrategy`, only emit `ToolResultEvent` when the result has actual search results:

```python
search_results = [r for r in result.results if isinstance(r, SearchResult)]
if on_event and search_results:
    on_event(ToolResultEvent(
        query=result.query,
        result_count=result.result_count,
        results=search_results,
    ))
```

**Rationale:** `ToolResultEvent` has `query: str`, `result_count: int`, `results: list[SearchResult]` — all search-specific. Page tools would produce `query=""`, `result_count=0`, `results=[]`, which is noise in verbose output. By checking `if search_results:` before emitting, page tool calls still get `ToolInvocationEvent` logged (showing the tool was called) but skip the meaningless result event.

### 3. Tool definitions as module constants in `app/chat.py`

**Decision:** Add two new constants alongside the existing `SEARCH_BOOK_TOOL`:

```python
GET_CURRENT_PAGE_TOOL = ToolDefinition(
    name="get_current_page",
    description="Get the reader's current page position in the book.",
    parameters={"type": "object", "properties": {}},
)

SET_CURRENT_PAGE_TOOL = ToolDefinition(
    name="set_current_page",
    description="Update the reader's current page position. Use when the reader tells you what page they are on.",
    parameters={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": "The page number the reader is currently on.",
            }
        },
        "required": ["page"],
    },
)
```

`get_current_page` has no required parameters. `set_current_page` has one required parameter: `page` (integer).

**Rationale:** Co-locating tool definitions with the use case that wires their handlers keeps the tool registration self-contained. All tools are passed to the strategy via `tools=[SEARCH_BOOK_TOOL, GET_CURRENT_PAGE_TOOL, SET_CURRENT_PAGE_TOOL]`.

### 4. BookRepository added to ChatWithBookUseCase

**Decision:** Add `book_repo: BookRepository` to the constructor. The `execute()` method uses it to create page tool handler closures.

**Rationale:** The use case already has `conversation_repo` and `message_repo`. Adding `book_repo` follows the same pattern. The page handlers need it to read `current_page` and persist changes from `set_current_page`.

### 5. AlwaysRetrieveStrategy unchanged

**Decision:** The `AlwaysRetrieveStrategy` already accepts `tool_handlers` and extracts only `search_book`. No changes needed — it doesn't run an agentic loop, so page tools are irrelevant to it.

**Rationale:** The always-retrieve strategy bypasses tool-use entirely. It reformulates the query and always searches. It receives the full `tool_handlers` dict but only uses `search_book`. The extra page tool entries are harmless.

### 6. System prompt update

**Decision:** Add the two new tools to the system prompt rules:

- `get_current_page`: Returns the reader's current page position. Use when you need to know where the reader is.
- `set_current_page`: Updates the reader's current page. Use when the reader tells you what page they're on (e.g., "I'm on page 50").

Add a rule: "When the reader mentions a page number in context of their reading position, use `set_current_page` to update it."

**Rationale:** The LLM needs explicit instructions on when to use each tool. Without guidance, it might call `get_current_page` on every turn or fail to recognize "I'm on page X" as a set-page intent.

## Risks / Trade-offs

**[Trade-off] set_current_page has immediate side effects** → Unlike search (which is read-only), `set_current_page` persists a change to the book entity. If the LLM misinterprets a page number, the user's position changes. This is acceptable because: (a) users can correct it by saying the right page, (b) page 0 resets, and (c) it matches the CLI `set-page` behavior.

**[Trade-off] ToolResult carries meaningless fields for page tools** → `query=""` and `result_count=0` are semantically empty. This is the cost of keeping a uniform handler return type. If more non-search tools are added later, consider introducing a leaner base result type. For now, the uniform type is simpler than a Union.

**[Risk] AlwaysRetrieveStrategy assumes search handler exists** → If `tool_handlers` doesn't contain `"search_book"`, the always-retrieve strategy would fail. This is acceptable because the chat use case always registers all three handlers.
