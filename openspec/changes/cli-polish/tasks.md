## 1. Domain: Token Usage & Chat Events

- [ ] 1.1 Add `TokenUsage` frozen dataclass to `domain/tool.py` (`input_tokens: int`, `output_tokens: int`)
- [ ] 1.2 Add `usage: TokenUsage | None = None` field to `ChatResponse` in `domain/tool.py`
- [ ] 1.3 Create `domain/chat_event.py` with `ToolInvocationEvent`, `ToolResultEvent`, `TokenUsageEvent` dataclasses and `ChatEvent` type alias
- [ ] 1.4 Write tests for domain value objects (TokenUsage, ChatResponse with usage, ChatEvent types)

## 2. Chat Provider: Token Usage

- [ ] 2.1 Update Anthropic adapter `chat_with_tools()` to read `response.usage.input_tokens` / `output_tokens` and populate `ChatResponse.usage`
- [ ] 2.2 Write tests for Anthropic adapter token usage population

## 3. Retrieval Strategy: Event Callback

- [ ] 3.1 Add `on_event: Callable[[ChatEvent], None] | None = None` parameter to `RetrievalStrategy` protocol in `domain/protocols.py`
- [ ] 3.2 Update `infra/retrieval/tool_use.py` `RetrievalStrategy.execute()` to accept `on_event` and emit `ToolInvocationEvent`, `ToolResultEvent`, and `TokenUsageEvent`
- [ ] 3.3 Update `infra/retrieval/always_retrieve.py` `RetrievalStrategy.execute()` to accept `on_event` and emit events
- [ ] 3.4 Write tests for tool-use strategy event emission
- [ ] 3.5 Write tests for always-retrieve strategy event emission

## 4. Chat Use Case: Event Callback

- [ ] 4.1 Add `on_event: Callable[[ChatEvent], None] | None = None` parameter to `ChatWithBookUseCase.__init__()`
- [ ] 4.2 Pass `on_event` through to `self._retrieval.execute()` call
- [ ] 4.3 Write tests for ChatWithBookUseCase event passthrough

## 5. Book Ingestion: Auto-Embed

- [ ] 5.1 Add optional `embed_use_case` parameter to `IngestBookUseCase.__init__()`
- [ ] 5.2 Call `embed_use_case.execute(book.id)` after successful chunking; catch embed errors and return `tuple[Book, Exception | None]` (return type change from `Book`)
- [ ] 5.3 Write tests: ingest with auto-embed success returns `(book, None)`, ingest with auto-embed failure returns `(book, exception)` with book in READY status, ingest without embed_use_case returns `(book, None)` (unchanged behavior wrapped in tuple)

## 6. CLI: Ingest Command Polish

- [ ] 6.1 Update `ingest` command to construct `EmbedBookUseCase` when `OPENAI_API_KEY` is available and pass it to `IngestBookUseCase`
- [ ] 6.2 Update `ingest` output: show embedding info on success, tip on no API key, warning on embed failure
- [ ] 6.3 Add verbose output to `ingest`: chunk count after ingest, embedding batch progress (no page count — not worth the plumbing)
- [ ] 6.4 Write tests for ingest CLI (auto-embed wiring, output messages, verbose output)

## 7. CLI: Embed Command Polish

- [ ] 7.1 Add chunk count to `embed` command output (`Chunks: N`)
- [ ] 7.2 Add verbose output to `embed`: chunk count before embedding, batch progress
- [ ] 7.3 Write tests for embed CLI output changes

## 8. CLI: Chat Verbose & Conversation Re-prompt

- [ ] 8.1 Wire `on_event` callback in `chat` command — print `[verbose]` lines for each `ChatEvent` type when `_verbose` is True
- [ ] 8.2 Update `_select_or_create_conversation` to loop on invalid input (max 3 retries)
- [ ] 8.3 Write tests for chat verbose event printing
- [ ] 8.4 Write tests for conversation selection re-prompt loop

## 9. Documentation

- [ ] 9.1 Update `README.md`: replace `ask` with `chat`, update API key table, update usage examples, update typical workflow, update architecture section (add `ChatWithBookUseCase`, `Conversation`, remove `AskBookUseCase`)

## 10. Verification

- [ ] 10.1 Run `uv run ruff check .` — fix any lint errors
- [ ] 10.2 Run `uv run pytest -x` — all tests pass
- [ ] 10.3 Run `uv run pyright` — zero type errors
