## Context

The agentic chat loop currently supports a single tool (`search_book`). The `RetrievalStrategy` protocol accepts `search_fn: Callable[[str], list[SearchResult]]` — a callback tightly coupled to the search tool's signature. Adding page tools requires generalizing this to dispatch multiple tools with different parameter shapes.

The `Book` entity already has `current_page` with `set_current_page(page)` domain logic and validation. The `BookRepository` protocol already has `save()` and `get()`. No new domain concepts or DB changes are needed — this change wires existing domain capabilities into the chat tool system.

## Goals / Non-Goals

**Goals:**

- Add `get_current_page` tool: LLM can read the book's current page position
- Add `set_current_page` tool: LLM can update the page position when the user says where they are
- Generalize `RetrievalStrategy` protocol from `search_fn` to a `tool_handlers` dispatch map
- Update both strategy implementations (`tool_use.py`, `always_retrieve.py`) to the new signature
- Give `ChatWithBookUseCase` access to `BookRepository` for page tool handlers
- Update conversation system prompt to describe the new tools

**Non-Goals:**

- Adding a `read_page` tool that fetches raw page text (future work)
- Changing how `current_page` filters search results (existing behavior preserved)
- Adding new event types for page tools (existing `ToolInvocationEvent` is sufficient)

## Decisions

### 1. Tool handler type: `Callable[[dict[str, object]], str]`

**Decision:** Define a `ToolHandler` type alias:

```python
ToolHandler = Callable[[dict[str, object]], str]
```

Each handler receives the tool's arguments dict and returns a string result to send back to the LLM. The strategy dispatches by looking up `invocation.tool_name` in a `dict[str, ToolHandler]` map.

**Rationale:** This is the minimum abstraction that supports tools with different parameter shapes. The strategy doesn't need to know what each tool does — it just routes invocations to handlers and passes the string result back. Handlers are closures defined in `ChatWithBookUseCase.execute()`, capturing `book_id`, repos, and `on_event`.

**Alternatives considered:**

- Keep `search_fn` and add `page_fn` parameters: not extensible — every new tool adds a parameter
- Rich `ToolResult` return type with structured data: over-engineering — a string is what the LLM needs
- Handler protocol class instead of callable: unnecessary ceremony for stateless functions

### 2. RetrievalStrategy protocol signature change

**Decision:** Replace `search_fn: Callable[[str], list[SearchResult]]` with `tool_handlers: dict[str, ToolHandler]`:

```python
class RetrievalStrategy(Protocol):
    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        tool_handlers: dict[str, Callable[[dict[str, object]], str]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]: ...
```

**Rationale:** The protocol should be tool-agnostic. The strategy receives tool definitions (what tools exist) and handlers (how to execute them) without knowing the details of any specific tool.

### 3. Event emission moves to handlers

**Decision:** The strategy emits only `ToolInvocationEvent` (before calling a handler) and `TokenUsageEvent` (after LLM calls). The search-specific `ToolResultEvent` is emitted by the search handler itself, which captures `on_event` via closure.

**Rationale:** `ToolResultEvent` has `results: list[SearchResult]` — search-specific structured data that the strategy can't produce from a string handler return. Moving the event emission into the search handler keeps event data rich without forcing the generic handler interface to carry search-specific types. Page tool calls still get `ToolInvocationEvent` logged in verbose mode.

### 4. Tool definitions as module constants

**Decision:** Define all three tools as constants in `app/chat.py`:

```python
SEARCH_BOOK_TOOL = ToolDefinition(name="search_book", ...)
GET_CURRENT_PAGE_TOOL = ToolDefinition(name="get_current_page", ...)
SET_CURRENT_PAGE_TOOL = ToolDefinition(name="set_current_page", ...)
```

`get_current_page` has no required parameters. `set_current_page` has one required parameter: `page` (integer).

**Rationale:** Co-locating tool definitions with the use case that wires their handlers keeps the tool registration self-contained. All tools are passed to the strategy via `tools=[SEARCH_BOOK_TOOL, GET_CURRENT_PAGE_TOOL, SET_CURRENT_PAGE_TOOL]`.

### 5. AlwaysRetrieveStrategy adaptation

**Decision:** The `AlwaysRetrieveStrategy` changes its signature to accept `tool_handlers` but continues to call only the search handler internally. It extracts the search handler via `tool_handlers["search_book"]` and calls it with `{"query": reformulated_query}`.

**Rationale:** The always-retrieve strategy bypasses tool-use — it reformulates the query and always searches. It doesn't need page tools since it doesn't run an agentic loop. But the protocol signature must match.

### 6. System prompt update

**Decision:** Add the two new tools to the system prompt rules:

- `get_current_page`: Returns the reader's current page position. Use when you need to know where the reader is.
- `set_current_page`: Updates the reader's current page. Use when the reader tells you what page they're on (e.g., "I'm on page 50").

Add a rule: "When the reader mentions a page number in context of their reading position, use `set_current_page` to update it."

**Rationale:** The LLM needs explicit instructions on when to use each tool. Without guidance, it might call `get_current_page` on every turn or fail to recognize "I'm on page X" as a set-page intent.

### 7. BookRepository added to ChatWithBookUseCase

**Decision:** Add `book_repo: BookRepository` to the constructor. The `execute()` method uses it to create page tool handler closures.

**Rationale:** The use case already has `conversation_repo` and `message_repo`. Adding `book_repo` follows the same pattern. The spec (CA-1) already lists `BookRepository` as a constructor dependency.

## Risks / Trade-offs

**[Trade-off] set_current_page has immediate side effects** → Unlike search (which is read-only), `set_current_page` persists a change to the book entity. If the LLM misinterprets a page number, the user's position changes. This is acceptable because: (a) users can correct it by saying the right page, (b) page 0 resets, and (c) it matches the CLI `set-page` behavior.

**[Trade-off] ToolResultEvent no longer emitted by strategy** → Verbose mode search logging still works because the search handler emits it. But the strategy is no longer responsible for result events, which is a shift in responsibility. If a future tool needs structured events, its handler can emit them the same way.

**[Risk] AlwaysRetrieveStrategy assumes search handler exists** → If `tool_handlers` doesn't contain `"search_book"`, the always-retrieve strategy would fail. This is acceptable because the chat use case always registers all three handlers.
