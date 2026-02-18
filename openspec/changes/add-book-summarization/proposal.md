## Why

When a user starts a chat session about a book, they currently see no overview — they jump straight into a blank conversation. A book summarization feature gives users an immediate structural understanding: what sections/headers exist, which pages they span, and what key statements each section contains. This orients the reader and helps them ask better questions during chat.

## What Changes

- Add a `SummarizeBookUseCase` in the application layer that uses the `ChatProvider` to generate per-section summaries from chunks
- Add a `summarize` CLI command that outputs a structured summary (headers, page ranges, key statements)
- Add a summarization prompt template in `shared/prompts/`
- Display the summary automatically when starting a new chat conversation (with opt-out via `--no-summary`)
- Add domain value objects for the summary structure (`SectionSummary`)

## Capabilities

### New Capabilities

- `book-summarization`: LLM-powered per-section summaries with page ranges and key statements

### Modified Capabilities

- `cli-commands`: Add `summarize` command; modify `chat` command to show summary on new conversations
- `chat-agent`: Inject summary context into the system prompt for better-informed chat

## Impact

- **New files**: `app/summarize.py` (use case), `domain/section_summary.py` (value object), `shared/prompts/summarization_prompt.md`
- **Modified files**: `main.py` (CLI commands), `app/chat.py` (summary display integration)
- **No DB changes**: Summaries are generated on-demand, not persisted (can be cached later)
- **New dependency on ChatProvider**: Uses existing Anthropic adapter for LLM summarization
- **Backward compatible**: Summary display is opt-out; existing chat flow unchanged when `--no-summary` is passed
