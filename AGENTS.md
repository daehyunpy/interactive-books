# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

Interactive Books — a local-only iOS/macOS app for uploading books and chatting about them using RAG. No backend server.

## Key Docs

- `docs/product_brief.md` — why this product exists (market gap, vision, competitive positioning, expansion roadmap)
- `docs/product_requirements.md` — what to build (features, user stories, success criteria, privacy)
- `docs/technical_design.md` — how to build it (architecture, stack, decisions, cross-platform contracts)

Read all three before making changes.

## Current State

**Phases 1–5 complete.** Entering Phase 6 (Q&A / Agentic Chat).

The Python CLI can ingest books (PDF/TXT), generate embeddings, and run vector search with page filtering. The `AskBookUseCase` exists as a single-turn RAG pipeline but will be replaced by agentic conversation in Phase 6.

Build order: CLI first, bottom-up, one feature at a time.

| Phase | What               | Status   |
| ----- | ------------------ | -------- |
| 1     | Project scaffold   | Done     |
| 2     | DB schema          | Done     |
| 3     | Book ingestion     | Done     |
| 4     | Embeddings         | Done     |
| 5     | Retrieval          | Done     |
| 6     | Q&A (Agentic Chat) | **Next** |
| 7     | CLI polish         | —        |
| 8     | iOS/macOS app      | —        |

See `docs/technical_design.md` → "Build Order" for details on each phase. See "Directory Layout" for the full project tree.

### Phase 6: Agentic Chat

Phase 6 replaces single-turn RAG with an agentic conversation system. See `docs/technical_design.md` → "Tool-Use Support" and "Data Flow" for architecture details.

#### Key Decisions (already resolved — do not re-ask)

| Decision                 | Choice                                                                                                               |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Retrieval strategy       | Formal tool-use API (Anthropic/OpenAI). Pluggable `RetrievalStrategy` protocol.                                      |
| Context management       | Full conversation history in prompt, capped at N messages (N TBD). Pluggable `ConversationContextStrategy` protocol. |
| Session structure        | Multiple named conversations per book. Auto-generated title from first message; user can rename.                     |
| Domain entity name       | `Conversation` — NOT `Session`.                                                                                      |
| ChatMessage FK           | `conversation_id` only — NO `book_id` on ChatMessage. Book reachable via `message → conversation → book`.            |
| Multi-book conversations | One book per conversation for now. May evolve for multi-book queries later.                                          |
| Ollama tool-use          | Deferred post-MVP. Ollama falls back to always-retrieve.                                                             |
| Tool results visibility  | Hidden in production. Visible with `--verbose` (CLI) / debug toggle (app).                                           |
| CLI `ask` command        | Remove entirely (not released). Replace with `cli chat <book>`.                                                      |
| Feature naming           | "Book Conversations" — ubiquitous language is "conversation", not "question" or "ask".                               |

#### Tasks

Build order is bottom-up, TDD (write failing tests first). Each task is one commit.

- [ ] **6.1 Schema migration** — Update `shared/schema/001_initial.sql`: add `conversations` table (`id`, `book_id`, `title`, `created_at`), change `chat_messages.book_id` → `conversation_id` FK, add `'tool_result'` to role CHECK constraint. Modify in-place (nothing released).
- [ ] **6.2 Domain: Conversation aggregate** — Create `domain/conversation.py` with `Conversation` entity (id, book_id, title, created_at). Validate non-empty title. Tests in `tests/domain/test_conversation.py`.
- [ ] **6.3 Domain: Update ChatMessage** — In `domain/chat.py`, replace `book_id` with `conversation_id`. Add `TOOL_RESULT` to `MessageRole`. Update `tests/domain/test_chat.py`.
- [ ] **6.4 Domain: Update errors** — Add `UNSUPPORTED_FEATURE` to `LLMErrorCode` in `domain/errors.py`.
- [ ] **6.5 Domain: New protocols** — In `domain/protocols.py`, add: `ConversationRepository`, `ChatMessageRepository`, `RetrievalStrategy`, `ConversationContextStrategy`. Extend `ChatProvider` with `chat_with_tools(messages, tools) -> ChatResponse`.
- [ ] **6.6 Domain: Tool-use value objects** — Add `ToolDefinition`, `ToolInvocation`, `ChatResponse` to domain (in `domain/tool_use.py` or extend `domain/prompt_message.py`).
- [ ] **6.7 Infra: ConversationRepository** — SQLite implementation in `infra/storage/conversation_repo.py`. Tests in `tests/infra/storage/test_conversation_repo.py`.
- [ ] **6.8 Infra: ChatMessageRepository** — SQLite implementation in `infra/storage/chat_message_repo.py`. Tests in `tests/infra/storage/test_chat_message_repo.py`.
- [ ] **6.9 Infra: Anthropic tool-use** — Implement `chat_with_tools()` in `infra/llm/anthropic.py` using Anthropic's tool-use API. Tests in `tests/infra/llm/test_anthropic_chat.py`.
- [ ] **6.10 Infra: RetrievalStrategy implementations** — `infra/strategies/tool_use_retrieval.py` (default) and `infra/strategies/always_retrieve.py` (Ollama fallback). Tests for each.
- [ ] **6.11 Infra: ConversationContextStrategy** — `infra/strategies/full_history_context.py` (full history, capped at N). Tests.
- [ ] **6.12 Prompt templates** — Create `shared/prompts/conversation_system_prompt.md` (agentic system prompt with tool-use instructions) and `shared/prompts/reformulation_prompt.md` (query reformulation).
- [ ] **6.13 App: ChatWithBookUseCase** — Agent loop in `app/chat.py`: build messages from conversation history → call `chat_with_tools()` → execute tool if invoked → persist turn → return response. Tests in `tests/app/test_chat.py`.
- [ ] **6.14 Remove AskBookUseCase** — Delete `app/ask.py` and `tests/app/test_ask.py`. Nothing released, clean removal.
- [ ] **6.15 CLI: Replace `ask` with `chat`** — In `main.py`, remove `ask` command, add `chat <book>` with interactive conversation loop, session persistence, `--verbose` for tool results.
- [ ] **6.16 End-to-end verification** — Run full pipeline: ingest → embed → `cli chat` → multi-turn conversation. Verify tool-use, context awareness, persistence.

#### What Exists Today (reference for implementation)

| Component               | File                            | Status                                            |
| ----------------------- | ------------------------------- | ------------------------------------------------- |
| `ChatMessage` model     | `domain/chat.py`                | Defined but uses `book_id` (needs update in 6.3)  |
| `MessageRole` enum      | `domain/chat.py`                | USER, ASSISTANT (needs TOOL_RESULT in 6.3)        |
| `ChatProvider` protocol | `domain/protocols.py`           | `chat()` only (needs `chat_with_tools()` in 6.5)  |
| `PromptMessage`         | `domain/prompt_message.py`      | Exists, usable as-is                              |
| `SearchBooksUseCase`    | `app/search.py`                 | Exists — becomes the tool the agent invokes       |
| `AskBookUseCase`        | `app/ask.py`                    | Will be replaced by `ChatWithBookUseCase` (6.14)  |
| `chat_messages` table   | `shared/schema/001_initial.sql` | Has `book_id` FK (needs `conversation_id` in 6.1) |
| Anthropic adapter       | `infra/llm/anthropic.py`        | `chat()` only (needs `chat_with_tools()` in 6.9)  |
| Prompt templates        | `shared/prompts/`               | 3 files exist; 2 new needed (6.12)                |

## First-Time Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [direnv](https://direnv.net/) — required for loading environment variables

### Python CLI

```bash
cp .env.example .env          # fill in API keys (see below)
cp .envrc.example .envrc      # direnv config
direnv allow                  # or: eval "$(direnv export zsh)"
cd python/
uv sync                       # install dependencies
uv run pytest -x              # verify everything works
```

### Environment Variables

| Variable            | Required | Notes                                                  |
| ------------------- | -------- | ------------------------------------------------------ |
| `ANTHROPIC_API_KEY` | Yes      | Default chat provider                                  |
| `OPENAI_API_KEY`    | No       | For OpenAI embeddings or chat                          |
| `OLLAMA_BASE_URL`   | No       | Local LLM endpoint (default: `http://localhost:11434`) |
| `MILVUS_ADDRESS`    | No       | Milvus vector DB address for claude-context MCP        |
| `MILVUS_TOKEN`      | No       | Milvus authentication token                            |

### Swift App (Phase 8)

Setup instructions will be added when the Swift app is scaffolded.

## Quick Commands

All Python commands run from `python/`. All Swift commands run from `swift/` (Phase 8).

| Task                | Command                     |
| ------------------- | --------------------------- |
| Install Python deps | `uv sync`                   |
| Run Python tests    | `uv run pytest -x`          |
| Lint Python         | `uv run ruff check .`       |
| Format Python       | `uv run ruff format .`      |
| Type check Python   | `uv run pyright`            |
| Run Swift tests     | `swift test` _(Phase 8)_    |
| Lint Swift          | `swiftlint` _(Phase 8)_     |
| Format Swift        | `swiftformat .` _(Phase 8)_ |

## Coding Disciplines

This project follows three disciplines: **DDD**, **TDD**, and **Clean Code**. These govern how every line of code is written, not just how folders are organized.

### DDD (Domain-Driven Design)

- **Ubiquitous language** — use domain terms consistently. A `Book` is a `Book`, not a `Document` or `Item`. A `Chunk` is a `Chunk`, not a `Segment` or `Fragment`. If the domain term changes, rename everywhere.
- **Entities vs Value Objects** — entities have identity (`Book` has an ID, persists, tracks state). Value objects are immutable data with no identity (`PageRange`, `ChunkMetadata`, `EmbeddingVector`). Don't give value objects IDs.
- **Aggregates** — `Book` and `Conversation` are aggregate roots. Access `Chunk`s through `Book`, `ChatMessage`s through `Conversation`. Don't let outside code reach into aggregate internals.
- **Domain logic in domain objects** — not in controllers, CLI handlers, or UI code. If you're writing an `if` about book state in a command handler, it belongs in the domain layer.
- **Domain layer has no outward dependencies** — domain code never imports infrastructure (DB, API clients, file I/O). It depends only on protocols/interfaces.
- **Domain errors** — use `BookError`, `LLMError`, `StorageError`. Let them propagate to the application layer.

### TDD (Test-Driven Development)

- **Red → Green → Refactor** — every feature and bug fix starts with a failing test.
- **Test naming** — describe behavior: `test_search_excludes_chunks_beyond_current_page`, not `test_search_method`.
- **Test structure** — Arrange-Act-Assert (Python) / Given-When-Then (Swift). One assertion per test where practical.
- **Unit tests** — domain logic in isolation, mock infrastructure. **Integration tests** — verify adapters work with real dependencies. **No tests for trivial code** — don't test getters, data classes, or framework glue.
- **Test location** — tests live in a separate `tests/` directory that mirrors the `source/` structure (e.g., `tests/domain/test_book.py` tests `source/.../domain/book.py`).
- **Protocols enable testing** — every protocol (`ChatProvider`, `BookParser`, etc.) should have a test double.

### Clean Code

- **Port naming** — domain Protocol classes keep clean names (`BookRepository`, not `BookRepositoryPort`). Infra adapters alias at import: `from ...protocols import BookRepository as BookRepositoryPort`. Never rename the protocol definition itself.
- **Adapter naming** — infra adapter classes use the same name as their domain protocol. The module path provides disambiguation (e.g., `infra.parsers.pdf.BookParser` implements `domain.protocols.BookParser`). Don't encode implementation details in the class name — use the module path instead (`parsers.pdf`, not `PyMuPdfParser`). When two implementations coexist at a call site, use import aliases (`from ...pdf import BookParser as PdfBookParser`).
- **Naming** — names reveal intent. `chunks_up_to_page(page)` not `get_filtered(p)`. Booleans read as assertions: `is_ingested`, `has_embeddings`.
- **Functions** — do one thing. If it has "and" in its description, split it. Aim for < 20 lines.
- **No empty `__init__.py`** — don't create empty `__init__.py` files. The project uses implicit namespace packages; they're unnecessary.
- **No dead code** — no commented-out code, no unused imports. Delete it; git remembers.
- **No magic values** — `MAX_CHUNK_TOKENS = 500`, not bare `500`.
- **Dependency direction** — UI → App → Domain ← Infra. Never reverse.
- **Single level of abstraction** — high-level functions call named functions; don't mix orchestration with details.
- **Early return** — guard clauses over nested `if/else`.
- **Immutability by default** — `let` over `var` (Swift), avoid mutation where practical (Python).

## What NOT to Do

- Don't add a backend server, remote database, or web interface
- Don't target below iOS 26 / macOS 26
- Don't use Core Data — we use SwiftData
- Don't hardcode a single LLM provider — always go through the protocol abstraction
- Don't write code without a failing test first
- Don't put domain logic in `infra/` or UI layers
- Don't let domain code import `infra/` modules
- Don't leave dead code, commented-out code, or unused imports
- Don't use magic numbers or strings — name them
- Don't add DB columns, domain concepts, or error cases without updating the shared contracts first (see `docs/technical_design.md` → "Cross-Platform Contracts")
- Don't change prompt templates in one codebase without updating `shared/prompts/`
- Don't put `book_id` on `ChatMessage` — it belongs on `Conversation`; access book via `message → conversation → book`
- Don't use "session" as a domain entity name — use `Conversation`
- Don't use "ask" for the CLI conversation command — it's `chat`

## Git Workflow (Gitflow)

- **`main`** — production-ready code. Only receives merges from `release/` and `hotfix/` branches.
- **`develop`** — integration branch. All feature branches merge here.
- **`feature/<name>`** — branch off `develop` for new features. Merge back to `develop` via PR.
- **`release/<version>`** — branch off `develop` when preparing a release. Merge to both `main` and `develop` when done.
- **`hotfix/<name>`** — branch off `main` for urgent fixes. Merge to both `main` and `develop`.
- **Commit style** — conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- **Keep commits focused** — one logical change per commit. Separate unrelated changes into separate commits.
- **No direct pushes** to `main` or `develop`.

## OpenSpec

This project uses OpenSpec for spec-driven development. All non-trivial changes go through this workflow. Trivial fixes (typos, single-line bugs) can skip it.

| Step | Command            | What it does                                                                  |
| ---- | ------------------ | ----------------------------------------------------------------------------- |
| 1    | `/opsx:new <name>` | Create a new change with a kebab-case name (e.g., `/opsx:new add-pdf-parser`) |
| 2    | `/opsx:ff`         | Generate all spec artifacts (requirements, design, tasks) in one pass         |
| 3    | `/opsx:apply`      | Implement the tasks from the generated spec                                   |
| 4    | `/opsx:verify`     | Verify implementation matches the spec artifacts                              |
| 5    | `/opsx:archive`    | Archive the completed change                                                  |

Artifacts are stored in `openspec/changes/` during development and moved to `openspec/changes/archive/` when done.
