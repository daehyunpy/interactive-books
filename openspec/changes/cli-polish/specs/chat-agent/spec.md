# chat-agent

Delta spec for adding event callback observability to `ChatWithBookUseCase`. The use case emits `ChatEvent` objects at key moments so the CLI (or other callers) can observe tool invocations, search results, and token usage.

## ADDED Requirements

### Requirement: ChatEvent value objects for observability

The domain layer SHALL define the following frozen dataclasses in `domain/chat_event.py`:

- `ToolInvocationEvent(tool_name: str, arguments: dict[str, object])` — emitted when the retrieval strategy invokes a tool
- `ToolResultEvent(query: str, result_count: int, results: list[SearchResult])` — emitted when a tool invocation returns search results
- `TokenUsageEvent(input_tokens: int, output_tokens: int)` — emitted when an LLM call completes with token usage data

`ChatEvent` SHALL be a type alias: `ChatEvent = ToolInvocationEvent | ToolResultEvent | TokenUsageEvent`

#### Scenario: ToolInvocationEvent creation

- **WHEN** a `ToolInvocationEvent` is created with `tool_name="search_book"` and `arguments={"query": "test"}`
- **THEN** the event is a frozen dataclass with those fields

#### Scenario: TokenUsageEvent creation

- **WHEN** a `TokenUsageEvent` is created with `input_tokens=100` and `output_tokens=50`
- **THEN** the event is a frozen dataclass with those fields

## MODIFIED Requirements

### CA-1: ChatWithBookUseCase orchestrates agentic conversation (MODIFIED)

The `ChatWithBookUseCase.__init__()` SHALL accept an additional optional parameter `on_event: Callable[[ChatEvent], None] | None = None`. The use case stores this callback and calls it at key moments during `execute()`:

1. After each tool invocation by the retrieval strategy: emits `ToolInvocationEvent`
2. After each tool result is received: emits `ToolResultEvent`
3. After each LLM call that returns token usage: emits `TokenUsageEvent`

If `on_event` is `None`, no events are emitted (no-op).

The `on_event` callback is passed through to `RetrievalStrategy.execute()` so the strategy can emit tool invocation and result events during its internal loop.

**Changes from original:**
- Added `on_event` parameter to constructor
- Events emitted during execute() for tool invocations, results, and token usage
- `on_event` passed through to retrieval strategy

#### Scenario: Events emitted during tool-use turn

- **WHEN** `execute()` is called with `on_event` set and the LLM invokes a tool
- **THEN** `ToolInvocationEvent`, `ToolResultEvent`, and `TokenUsageEvent` are emitted via the callback

#### Scenario: No events when callback is None

- **WHEN** `execute()` is called with `on_event=None`
- **THEN** no events are emitted; behavior is otherwise identical

#### Scenario: Token usage emitted on direct response

- **WHEN** the LLM responds directly without tool use
- **THEN** only `TokenUsageEvent` is emitted (no tool events)
