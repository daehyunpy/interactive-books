## 1. Domain: Token Usage & Chat Events

- [x] 1.1 Add `TokenUsage` frozen dataclass to `domain/tool.py` (`input_tokens: int`, `output_tokens: int`)
- [x] 1.2 Add `usage: TokenUsage | None = None` field to `ChatResponse` in `domain/tool.py`
- [x] 1.3 Create `domain/chat_event.py` with `ToolInvocationEvent`, `ToolResultEvent`, `TokenUsageEvent` dataclasses and `ChatEvent` type alias
- [x] 1.4 Write tests for domain value objects (TokenUsage, ChatResponse with usage, ChatEvent types)

## 2. Chat Provider: Token Usage

- [x] 2.1 Update Anthropic adapter `chat_with_tools()` to read `response.usage.input_tokens` / `output_tokens` and populate `ChatResponse.usage`
- [x] 2.2 Write tests for Anthropic adapter token usage population

## 3. Retrieval Strategy: Event Callback

- [x] 3.1 Add `on_event: Callable[[ChatEvent], None] | None = None` parameter to `RetrievalStrategy` protocol in `domain/protocols.py`
- [x] 3.2 Update `infra/retrieval/tool_use.py` `RetrievalStrategy.execute()` to accept `on_event` and emit `ToolInvocationEvent`, `ToolResultEvent`, and `TokenUsageEvent`
- [x] 3.3 Update `infra/retrieval/always_retrieve.py` `RetrievalStrategy.execute()` to accept `on_event` and emit events
- [x] 3.4 Write tests for tool-use strategy event emission
- [x] 3.5 Write tests for always-retrieve strategy event emission

## 4. Chat Use Case: Event Callback

- [x] 4.1 Add `on_event: Callable[[ChatEvent], None] | None = None` parameter to `ChatWithBookUseCase.__init__()`
- [x] 4.2 Pass `on_event` through to `self._retrieval.execute()` call
- [x] 4.3 Write tests for ChatWithBookUseCase event passthrough

## 5. Book Ingestion: Auto-Embed

- [x] 5.1 Add optional `embed_use_case` parameter to `IngestBookUseCase.__init__()`
- [x] 5.2 Call `embed_use_case.execute(book.id)` after successful chunking; catch embed errors and return `tuple[Book, Exception | None]` (return type change from `Book`)
- [x] 5.3 Write tests: ingest with auto-embed success returns `(book, None)`, ingest with auto-embed failure returns `(book, exception)` with book in READY status, ingest without embed_use_case returns `(book, None)` (unchanged behavior wrapped in tuple)

## 6. CLI: Ingest Command Polish

- [x] 6.1 Update `ingest` command to construct `EmbedBookUseCase` when `OPENAI_API_KEY` is available and pass it to `IngestBookUseCase`
- [x] 6.2 Update `ingest` output: show embedding info on success, tip on no API key, warning on embed failure
- [x] 6.3 Add verbose output to `ingest`: chunk count after ingest, embedding batch progress (no page count — not worth the plumbing)
- [x] 6.4 Write tests for ingest CLI (auto-embed wiring, output messages, verbose output)

## 7. CLI: Embed Command Polish

- [x] 7.1 Add chunk count to `embed` command output (`Chunks: N`)
- [x] 7.2 Add verbose output to `embed`: chunk count before embedding, batch progress
- [x] 7.3 Write tests for embed CLI output changes

## 8. CLI: Chat Verbose & Conversation Re-prompt

- [x] 8.1 Wire `on_event` callback in `chat` command — print `[verbose]` lines for each `ChatEvent` type when `_verbose` is True
- [x] 8.2 Update `_select_or_create_conversation` to loop on invalid input (max 3 retries)
- [x] 8.3 Write tests for chat verbose event printing
- [x] 8.4 Write tests for conversation selection re-prompt loop

## 9. Documentation

- [x] 9.1 Update `README.md`: replace `ask` with `chat`, update API key table, update usage examples, update typical workflow, update architecture section (add `ChatWithBookUseCase`, `Conversation`, remove `AskBookUseCase`)

## 10. Verification

- [x] 10.1 Run `uv run ruff check .` — fix any lint errors
- [x] 10.2 Run `uv run pytest -x` — all tests pass
- [x] 10.3 Run `uv run pyright` — zero type errors
