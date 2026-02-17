# Interactive Books

A local-only app for uploading books and chatting about them using RAG. No backend server — your data stays on your device (except LLM API calls).

Upload a PDF or TXT, ingest and embed it, then ask questions scoped to your reading position so you never get spoiled.

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

| Variable            | Required | Used by                  |
| ------------------- | -------- | ------------------------ |
| `ANTHROPIC_API_KEY` | Yes      | `ask` (chat)             |
| `OPENAI_API_KEY`    | Yes      | `embed`, `search`, `ask` |

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
```

### Generate embeddings

```bash
uv run interactive-books embed <book-id>
```

This calls the OpenAI embeddings API to vectorize all chunks. Required before `search` or `ask`.

### Search a book

```bash
uv run interactive-books search <book-id> "What is the main argument?"
uv run interactive-books search <book-id> "chapter on ethics" --top-k 10
```

Returns ranked passages with page ranges and distance scores.

### Ask a question

```bash
uv run interactive-books ask <book-id> "What does the author say about free will?"
```

Uses RAG: searches for relevant passages, then sends them as context to Claude for a grounded answer with page citations.

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
uv run interactive-books set-page <book-id> 50    # search/ask scoped to pages 1-50
uv run interactive-books set-page <book-id> 0     # reset — all pages eligible
```

When a reading position is set, `search` and `ask` only return results from pages up to that position. This prevents spoilers.

### Delete a book

```bash
uv run interactive-books delete <book-id>          # prompts for confirmation
uv run interactive-books delete <book-id> --yes    # skip confirmation
```

Removes the book, its chunks, and embeddings.

### Verbose mode

Add `--verbose` before any command for extra output (model names, timing, result counts):

```bash
uv run interactive-books --verbose ask <book-id> "What happens in chapter 3?"
```

## Typical Workflow

```bash
# 1. Ingest
uv run interactive-books ingest ~/Books/thinking-fast-and-slow.pdf

# 2. Embed (one-time, takes ~30s depending on book size)
uv run interactive-books embed <book-id>

# 3. Set your reading position
uv run interactive-books set-page <book-id> 120

# 4. Ask away — answers scoped to pages 1-120
uv run interactive-books ask <book-id> "What are the two systems?"
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

- **Domain**: `Book`, `Chunk`, `BookSummary`, `SearchResult`, `PromptMessage` + protocol interfaces
- **Application**: `IngestBookUseCase`, `EmbedBookUseCase`, `SearchBooksUseCase`, `AskBookUseCase`, `ListBooksUseCase`, `DeleteBookUseCase`
- **Infrastructure**: SQLite + sqlite-vec for storage, OpenAI for embeddings, Anthropic for chat
- **CLI**: Typer commands in `main.py` — thin wiring that composes use cases

See `docs/technical_design.md` for full architecture details.
