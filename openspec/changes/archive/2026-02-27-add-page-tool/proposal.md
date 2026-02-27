## Why

The agentic chat system currently has one tool (`search_book`) — the LLM can search for passages but has no awareness of the reader's current page position. The `current_page` value exists on the `Book` entity and filters search results behind the scenes, but the LLM cannot read or change it. Users who want to update their reading position mid-conversation must exit the chat, run `set-page` from the CLI, and re-enter. This breaks the conversational flow.

Adding `get_current_page` and `set_current_page` tools lets the LLM:
- Answer "what page am I on?" directly
- Respond to "I'm on page 50" by calling `set_current_page` and adjusting its behavior
- Include the current page context when formulating answers (e.g. "As of your current position on page 42…")

This also means the system prompt's rule "Do not reveal or discuss content from pages beyond the reader's current position" becomes enforceable by the LLM itself — it can check the page before answering.

## What Changes

> **Note:** The summarization merge (`186b0b5`) already generalized the retrieval strategy from `search_fn` to `tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]]`. The `RetrievalStrategy` protocol, both strategy implementations, and the search handler in `ChatWithBookUseCase` all use this pattern. This change builds on that foundation.

- Define two new `ToolDefinition`s: `get_current_page` and `set_current_page`
- Add page tool handlers to `ChatWithBookUseCase` that return `ToolResult` (matching the existing search handler pattern)
- Give the chat use case access to `BookRepository` so it can read and persist page changes
- Guard `ToolResultEvent` emission in `ToolUseRetrievalStrategy` so non-search tools don't emit spurious search-specific events
- Update the conversation system prompt to describe the new tools and when to use them

## Capabilities

### Modified Capabilities

- `chat-tool-use`: Add `get_current_page` and `set_current_page` tool definitions; guard `ToolResultEvent` emission for non-search handlers
- `chat-agent`: Update `ChatWithBookUseCase` to accept `BookRepository`, register page tool handlers returning `ToolResult`, and pass all three tools to the retrieval strategy
- `prompt-templates`: Update `conversation_system_prompt.md` to describe the two new tools and their usage rules

## Impact

- **No new files**: All changes are in existing files
- **No new dependencies**: Uses existing infrastructure (`BookRepository`, `Book.set_current_page()`, `ToolResult`)
- **No DB changes**: `current_page` column already exists on the `books` table
- **No protocol change**: `RetrievalStrategy` protocol already uses `tool_handlers: dict[str, Callable[[dict[str, object]], ToolResult]]` (done in summarization merge)
- **Backward compatible in behavior**: Existing search functionality is preserved; new tools are additive
- **Side effect**: `set_current_page` persists the page change immediately, same as the CLI `set-page` command
