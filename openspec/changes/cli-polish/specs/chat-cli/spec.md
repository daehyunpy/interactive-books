# chat-cli

Delta spec for chat CLI verbose enhancements. The `chat` command's `--verbose` flag surfaces tool invocations, search results, and token usage via an event callback from `ChatWithBookUseCase`.

## MODIFIED Requirements

### CCLI-5: Verbose mode shows tool results (MODIFIED)

The `chat` command SHALL support `--verbose`. When enabled:

- Chat model name is displayed at the start of the session: `[verbose] Chat model: <name>`
- Tool invocations are printed inline: `[verbose] Tool call: <tool_name>(<key>=<value>, ...)`
- Tool result summaries are printed: `[verbose]   → N results (pages X-Y, ...)`
- Token usage is printed per turn: `[verbose] Tokens: X in / Y out`

The CLI achieves this by passing an `on_event` callback to `ChatWithBookUseCase`. The callback receives `ChatEvent` objects and prints the appropriate `[verbose]` line for each event type.

When `--verbose` is not set, `on_event` is `None` and no debug output is printed.

**Changes from original:**
- Added tool invocation detail printing (tool name and arguments)
- Added tool result summary printing (result count and page ranges)
- Added token usage printing per turn
- Implementation via `on_event` callback instead of direct access to internal state

#### Scenario: Verbose mode prints tool invocation details

- **WHEN** `cli chat <book-id> --verbose` is used and the LLM invokes `search_book` with query "protagonist motivations"
- **THEN** `[verbose] Tool call: search_book(query="protagonist motivations")` is printed

#### Scenario: Verbose mode prints tool result summary

- **WHEN** a tool invocation returns 3 results
- **THEN** `[verbose]   → 3 results (pages 12-14, 45-47, 89-91)` is printed

#### Scenario: Verbose mode prints token usage

- **WHEN** an LLM call completes with 1234 input tokens and 567 output tokens
- **THEN** `[verbose] Tokens: 1,234 in / 567 out` is printed

#### Scenario: Non-verbose hides all debug output

- **WHEN** `cli chat <book-id>` is used without `--verbose`
- **THEN** only the assistant response is printed; no `[verbose]` lines appear
