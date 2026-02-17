## Context

Phase 7 "CLI polish" — all CLI commands exist and work, but two significant gaps remain:

1. **`ingest` doesn't embed** — the spec and data flow say `ingest` should parse, chunk, and embed in one step, but it only parses and chunks. Users must manually run `embed` afterward with no hint.
2. **`--verbose` is mostly unimplemented** — the spec requires logging chunk boundaries, similarity scores, prompt construction, and token counts, but only `search` (elapsed time) and `embed` (retry) use the flag. `chat` only prints the model name.

Additionally, small UX rough edges: no chunk count in `embed` output, conversation selection silently creates new on invalid input.

The codebase has no callback/event mechanism for use cases to report intermediate state to the CLI layer. Verbose output requires plumbing events from deep in the call stack (LLM response metadata, tool invocations, search queries) up to `main.py`.

## Goals / Non-Goals

**Goals:**

- `ingest` does parse + chunk + embed in one shot (with graceful fallback if no API key)
- `--verbose` outputs meaningful debug info for every command that does something interesting
- Token usage from LLM calls is surfaced to the CLI
- `chat` verbose mode shows tool invocations, search results, and reformulated queries
- Small UX fixes (embed output, conversation re-prompt)

**Non-Goals:**

- Streaming responses (already noted as a feature in the spec, but not part of Phase 7 polish)
- Provider selection CLI flags (e.g., `--provider anthropic`) — deferred to when more providers exist
- Structured logging or log levels — `[verbose]` prefix is sufficient for a debug/proto CLI
- Removing the standalone `embed` command — it stays for re-embed and provider-switch scenarios

## Decisions

### 1. Event callback for verbose observability

**Decision:** Add an optional `on_event: Callable[[ChatEvent], None] | None` parameter to `ChatWithBookUseCase.__init__()`. The use case calls it at key moments; the CLI prints when `_verbose` is True.

**Alternatives considered:**

- Return a rich result object with all intermediate data → clutters the return type for non-verbose callers
- Logger-based approach → too heavy for a prototyping CLI, introduces a logging framework dependency
- Pass `verbose: bool` into use cases → leaks presentation concerns into application layer

**Event types** (simple dataclass union):

```python
@dataclass(frozen=True)
class ToolInvocationEvent:
    tool_name: str
    arguments: dict[str, object]

@dataclass(frozen=True)
class ToolResultEvent:
    query: str
    result_count: int
    results: list[SearchResult]

@dataclass(frozen=True)
class TokenUsageEvent:
    input_tokens: int
    output_tokens: int

ChatEvent = ToolInvocationEvent | ToolResultEvent | TokenUsageEvent
```

These live in `domain/chat_event.py` as value objects (no identity, immutable).

### 2. Token usage plumbing

**Decision:** Extend `ChatResponse` (in `domain/tool.py`) with an optional `usage: TokenUsage | None` field. The Anthropic adapter reads `response.usage.input_tokens` and `response.usage.output_tokens` from the API response and populates this field. `RetrievalStrategy` passes `ChatResponse` objects through to the use case, which emits `TokenUsageEvent` via `on_event`.

**`TokenUsage`** is a new frozen dataclass in `domain/tool.py`:

```python
@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
```

This avoids a new file — it naturally belongs with `ChatResponse`.

### 3. Auto-embed in ingest — return type

**Decision:** `IngestBookUseCase` accepts an optional `embed_use_case: EmbedBookUseCase | None = None`. After successful chunking, if `embed_use_case` is not None, it calls `embed_use_case.execute(book.id)`.

The return type changes from `Book` to `tuple[Book, Exception | None]`. The second element is:

- `None` if embedding succeeded or was not attempted
- The caught exception if embedding failed

This lets the CLI distinguish "ingest failed" from "ingest succeeded but embed failed" without exception flow for a non-fatal outcome. The book stays in READY status either way.

The CLI's `ingest` command:

- If `OPENAI_API_KEY` is set: constructs `EmbedBookUseCase` and passes it in → auto-embeds
- If not set: passes `None` → prints a hint: "Tip: set OPENAI_API_KEY and run `embed <book-id>` to enable search."
- If embed failed: prints a warning with the error message

**Alternatives considered:**

- Re-raise a distinct error code (e.g., `BookError(EMBEDDING_FAILED)`) → exception flow for non-fatal outcome is confusing; callers must distinguish fatal vs. non-fatal raises
- Always require API key for ingest → breaks existing workflow, blocks ingestion for users who only want parsing
- Separate orchestrator in main.py → duplicates try/catch logic, status transitions become the CLI's concern

### 4. Event plumbing through RetrievalStrategy

**Decision:** Add `on_event: Callable[[ChatEvent], None] | None = None` as an optional keyword argument to `RetrievalStrategy.execute()`. The strategy calls it when it invokes a tool, receives results, and gets token usage from `ChatResponse.usage`. The use case passes its own `on_event` through.

Updated protocol signature:

```python
class RetrievalStrategy(Protocol):
    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        search_fn: Callable[[str], list[SearchResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]: ...
```

Both `tool_use.RetrievalStrategy` and `always_retrieve.RetrievalStrategy` accept and call `on_event`. The parameter has a default of `None`, so existing callers and test doubles are unaffected.

**Alternatives considered:**

- Wrap `search_fn` in the use case to intercept events → only captures search results, not tool invocations or token usage from inside the strategy loop
- Return richer data from the strategy → clutters the return type for all callers
- Keep protocol unchanged, emit events only from the use case → use case doesn't see intermediate tool invocations (the strategy runs the loop internally)

### 5. Verbose output format

All verbose lines use the `[verbose]` prefix for easy grep-ability. Format:

```
[verbose] Chat model: claude-sonnet-4-5-20250929
[verbose] Tool call: search_book(query="protagonist motivations")
[verbose]   → 3 results (pages 12-14, 45-47, 89-91)
[verbose] Tokens: 1,234 in / 567 out
```

For `ingest`:

```
[verbose] Parsed 142 pages
[verbose] Chunked into 47 chunks (pages 1-142)
[verbose] Embedding batch 1/1 (47 chunks)
[verbose] Embedded 47 chunks via openai (dim=1536)
```

### 6. Conversation selection re-prompt

**Decision:** Wrap the selection input in a loop (max 3 attempts). On invalid input, print "Invalid choice, try again." and re-prompt. After 3 failures, create a new conversation (current behavior as fallback).

### 7. Ingest verbose — no callback, query after the fact

**Decision:** Don't add an `on_event` callback to `IngestBookUseCase`. The CLI queries chunk count via `chunk_repo.count_by_book()` after execution (it already does this). For embedding batch progress, the `EmbedBookUseCase` already accepts `on_retry` — we add a similar `on_progress: Callable[[int, int], None] | None` callback for batch progress that the CLI wires when verbose.

Page count is not surfaced — the use case doesn't return it, and adding it to the return type just for verbose isn't worth it. The chunk count and page range (from chunk metadata) are sufficient.

**Alternatives considered:**

- Add `on_event` to `IngestBookUseCase` (like chat) → over-engineered for a command that runs once and returns
- Return `tuple[Book, int, Exception | None]` with page count → clutters the return type for a rarely-needed value

## Risks / Trade-offs

- **[Risk] `on_event` callback adds complexity to protocol** → Mitigated by making it optional with `None` default. Existing tests pass without changes until they want to test event emission.
- **[Risk] Auto-embed in ingest could be slow for large books** → Mitigated by verbose output showing batch progress. The user sees activity, not a frozen terminal. No timeout needed — the embedding provider already has retry logic.
- **[Risk] Token usage depends on Anthropic-specific response fields** → Mitigated by the `TokenUsage` domain value object. Other providers will populate it from their own response format. The field is optional (`None` if provider doesn't support it).
- **[Trade-off] `on_event` on `RetrievalStrategy` changes the protocol** → Acceptable because the parameter has a default value; existing implementations need only add `**kwargs` or the parameter with default. No breaking change.
