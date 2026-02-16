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

**Pre-implementation.** No code written yet. Currently entering Phase 1 (Project Scaffold).

Build order: CLI first, bottom-up, one feature at a time.

| Phase | What             |
| ----- | ---------------- |
| 1     | Project scaffold |
| 2     | DB schema        |
| 3     | Book ingestion   |
| 4     | Embeddings       |
| 5     | Retrieval        |
| 6     | Q&A              |
| 7     | CLI polish       |
| 8     | iOS/macOS app    |

See `docs/technical_design.md` → "Build Order" for details on each phase. See "Directory Layout" for the full project tree.

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
- **Aggregates** — `Book` is an aggregate root. Access its `Chunk`s through `Book`, not independently. Don't let outside code reach into aggregate internals.
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
- **Naming** — names reveal intent. `chunks_up_to_page(page)` not `get_filtered(p)`. Booleans read as assertions: `is_ingested`, `has_embeddings`.
- **Functions** — do one thing. If it has "and" in its description, split it. Aim for < 20 lines.
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
