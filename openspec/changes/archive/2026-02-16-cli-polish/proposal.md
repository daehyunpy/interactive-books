## Why

Phase 7 requires all CLI commands to be working and polished. The core commands (`ingest`, `search`, `chat`, `books`, `embed`, `show`, `delete`, `set-page`) all exist, but several gaps remain:

1. **`ingest` doesn't embed** — the spec says `cli ingest <file>` should "parse, chunk, embed a book," but it only parses and chunks. Users must manually run `embed` as a separate step, with no hint that they should.
2. **`--verbose` is incomplete** — the spec requires logging "chunk boundaries, similarity scores, prompt construction, token counts," but most commands ignore the flag entirely. The `chat` command only prints the model name; it never surfaces tool invocations, reformulated queries, or token usage.
3. **Minor UX rough edges** — no "next steps" after ingest, no embed count in `embed` output, conversation selection doesn't re-prompt on invalid input.

## What Changes

- **Merge embed into ingest**: `ingest` calls `EmbedBookUseCase` after chunking (requires `OPENAI_API_KEY`). The standalone `embed` command stays for re-embedding scenarios.
- **Verbose output across all commands**: Add `[verbose]` logging for chunk boundaries (ingest), embedding batch progress (ingest/embed), tool invocations and results (chat), prompt construction summary (chat), and token counts (chat).
- **Token usage plumbing**: `ChatProvider.chat()` and `chat_with_tools()` return token usage info. `ChatWithBookUseCase` surfaces it via a callback or return value so the CLI can print it.
- **Chat verbose callbacks**: `ChatWithBookUseCase` accepts an optional event callback so the CLI can print tool invocations, search results, and reformulated queries in verbose mode.
- **Ingest output hints**: After successful ingest+embed, print chunk count and confirm the book is search-ready. If embed fails (e.g., missing API key), the book is still ingested — print a hint to run `embed` manually.
- **Embed output improvement**: Show number of chunks embedded in the summary.
- **Conversation selection re-prompt**: Loop on invalid input instead of silently creating a new conversation.

## Capabilities

### New Capabilities

- `cli-verbose`: Verbose output contract across all CLI commands — what each command logs with `--verbose`, token count display format, tool invocation display format.

### Modified Capabilities

- `cli-commands`: `ingest` command now includes embedding step; `embed` output shows chunk count; conversation selection re-prompts on invalid input.
- `book-ingestion`: `IngestBookUseCase` accepts optional `EmbedBookUseCase` dependency for auto-embedding after chunking.
- `chat-cli`: `--verbose` surfaces tool invocations, search results, reformulated queries, and token counts via event callback.
- `chat-agent`: `ChatWithBookUseCase` accepts optional event callback for verbose/debug observability.
- `chat-provider`: `chat()` and `chat_with_tools()` return token usage alongside the response.

## Impact

- **`main.py`** — `ingest` command gains embedding step and verbose output; `chat` command gains verbose event printing; `embed` command gains chunk count output; conversation selection loops on invalid input.
- **`app/ingest.py`** — `IngestBookUseCase` accepts optional `EmbedBookUseCase` for auto-embedding.
- **`app/chat.py`** — `ChatWithBookUseCase` accepts optional event callback; calls it on tool invocations, search results, and token usage.
- **`infra/llm/anthropic.py`** — `chat()` and `chat_with_tools()` return `ChatResponse` with token usage.
- **`domain/` value objects** — Add `TokenUsage` and `ChatResponse` (or similar) to carry usage data.
- **Tests** — Update existing tests for modified signatures; add tests for verbose output, auto-embed in ingest, re-prompt loop.
