# Interactive Books

A local-only app for uploading books and having conversations about them using agentic RAG. No backend server — your data stays on your device (except LLM API calls).

Upload a PDF or TXT, ingest and embed it, then chat about it with an AI that decides when to search your book for relevant passages. Set a reading position so you never get spoiled.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [direnv](https://direnv.net/) (for loading environment variables)

## Setup

```bash
cp .env.example .env          # fill in API keys
cp .envrc.example .envrc
direnv allow

cd python/
uv sync
```

### API Keys

| Variable            | Required | Used by                                   |
| ------------------- | -------- | ----------------------------------------- |
| `ANTHROPIC_API_KEY` | Yes      | `chat` (conversation with Claude)         |
| `OPENAI_API_KEY`    | Yes      | `embed`, `search`, `chat` (vector search) |

Setting `OPENAI_API_KEY` also enables auto-embedding during `ingest`.

## Usage

All commands run from the `python/` directory using `uv run interactive-books`.

### Ingest a book

```bash
uv run interactive-books ingest path/to/book.pdf
uv run interactive-books ingest path/to/book.txt --title "Custom Title"
```

Output:

```
Book ID:     a1b2c3d4-...
Title:       book
Status:      ready
Chunks:      42
Embedded:    openai
```

If `OPENAI_API_KEY` is set, embeddings are generated automatically. Otherwise you'll see a tip to run `embed` separately.

### Generate embeddings

```bash
uv run interactive-books embed <book-id>
```

This calls the OpenAI embeddings API to vectorize all chunks. Required before `search` or `chat`. If you used `ingest` with `OPENAI_API_KEY` set, this was already done.

### Search a book

```bash
uv run interactive-books search <book-id> "What is the main argument?"
uv run interactive-books search <book-id> "chapter on ethics" --top-k 10
```

Returns ranked passages with page ranges and distance scores.

### Chat about a book

```bash
uv run interactive-books chat <book-id>
```

Starts an interactive conversation. The AI agent decides when to search for relevant passages and reformulates queries using conversation context. Conversations are persisted — you can resume where you left off.

```
Existing conversations:
  [1] What are the two systems? (a1b2c3d4...)
  [N] New conversation
Select [N]: 1
Conversation: What are the two systems? (a1b2c3d4...)
Type your message (or 'quit' to exit).

You: What does the author say about cognitive biases?
Assistant: The author discusses cognitive biases extensively...
```

### List all books

```bash
uv run interactive-books books
```

Output:

```
ID                                     Title                          Status     Chunks Provider       Page
------------------------------------------------------------------------------------------------------
a1b2c3d4-...                           My Book                        ready          42 openai            0
```

### Show book details

```bash
uv run interactive-books show <book-id>
```

### Set reading position

```bash
uv run interactive-books set-page <book-id> 50    # search/chat scoped to pages 1-50
uv run interactive-books set-page <book-id> 0     # reset — all pages eligible
```

When a reading position is set, `search` and `chat` only return results from pages up to that position. This prevents spoilers.

### Delete a book

```bash
uv run interactive-books delete <book-id>          # prompts for confirmation
uv run interactive-books delete <book-id> --yes    # skip confirmation
```

Removes the book, its chunks, conversations, and embeddings.

### Verbose mode

Add `--verbose` before any command for extra output (tool calls, retrieved passages, token counts):

```bash
uv run interactive-books --verbose chat <book-id>
```

In chat, verbose mode shows:

- `[verbose] Tool call: search_book(...)` — when the agent decides to search
- `[verbose] Retrieved N passages for: ...` — search results
- `[verbose] Tokens: N in, N out` — token usage per LLM call

## Typical Workflow

```bash
# 1. Ingest (auto-embeds if OPENAI_API_KEY is set)
uv run interactive-books ingest ~/Books/thinking-fast-and-slow.pdf

# 2. Embed (skip if auto-embedded during ingest)
uv run interactive-books embed <book-id>

# 3. Set your reading position
uv run interactive-books set-page <book-id> 120

# 4. Chat — multi-turn conversation scoped to pages 1-120
uv run interactive-books chat <book-id>
```

## Development

```bash
cd python/
uv run pytest -x         # run tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run pyright           # type check
```

## Architecture

The project follows DDD (Domain-Driven Design) with clean layering:

```
UI (CLI) -> Application (Use Cases) -> Domain (Entities, Protocols) <- Infrastructure (SQLite, APIs)
```

- **Domain**: `Book`, `Chunk`, `Conversation`, `ChatMessage`, `SearchResult`, `ChatEvent` + protocol interfaces
- **Application**: `IngestBookUseCase`, `EmbedBookUseCase`, `SearchBooksUseCase`, `ChatWithBookUseCase`, `ManageConversationsUseCase`, `ListBooksUseCase`, `DeleteBookUseCase`
- **Infrastructure**: SQLite + sqlite-vec for storage, OpenAI for embeddings, Anthropic for chat (tool-use agent)
- **CLI**: Typer commands in `main.py` — thin wiring that composes use cases

The chat agent uses Anthropic's tool-use API with a pluggable `RetrievalStrategy` to decide when to search the book. A `ConversationContextStrategy` manages how conversation history is included in the prompt.

See `docs/technical_design.md` for full architecture details.
