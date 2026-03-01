# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

Interactive Books — a local-only iOS/macOS/visionOS app for uploading books and chatting about them using RAG. No backend server.

## Key Docs

- `docs/product_brief.md` — why this product exists (market gap, vision, competitive positioning, expansion roadmap)
- `docs/product_requirements.md` — what to build (features, user stories, success criteria, privacy)
- `docs/technical_design.md` — how to build it (architecture, stack, decisions, cross-platform contracts)
- `docs/app_build_plan.md` — Phase 10 breakdown (Phases A–N for the iOS/macOS/visionOS Swift app)

Read all four before making changes to the Swift app.

## Current State

**Phases 1–9 complete.** The Python CLI is fully functional with all planned format support.

The Python CLI can ingest books (PDF, TXT, EPUB, DOCX, HTML, Markdown, and URLs), generate embeddings, run vector search, and have multi-turn agentic conversations about books. The agent decides when to retrieve via tool-use, maintains conversation history, and persists sessions.

**Phase 10 in progress:** iOS/macOS/visionOS app — Phases A–C done, Phase D next.

Build order: CLI first, bottom-up, one feature at a time.

| Phase | What                      | Status         |
| ----- | ------------------------- | -------------- |
| 1     | Project scaffold          | Done           |
| 2     | DB schema                 | Done           |
| 3     | Book ingestion            | Done           |
| 4     | Embeddings                | Done           |
| 5     | Retrieval                 | Done           |
| 6     | Q&A (Agentic Chat)        | Done           |
| 7     | CLI polish                | Done           |
| 8     | Structured format parsers | Done           |
| 9     | Text format parsers       | Done           |
| 10    | iOS/macOS/visionOS app    | **In Progress** |

### Phase 10 Sub-Phases

| Sub-Phase | What                  | Status   |
| --------- | --------------------- | -------- |
| A         | Project scaffold      | Done     |
| B         | Domain layer          | Done     |
| C         | Storage layer         | Done     |
| D         | sqlite-vec integration | **Next** |
| E–N       | Remaining phases      | Pending  |

See `docs/app_build_plan.md` for the full Phase A–N breakdown.
See `docs/technical_design.md` → "Build Order" for details on each phase. See "Directory Layout" for the full project tree.

### Agentic Chat Architecture (Phase 6 — completed)

The conversation system uses tool-use to let the LLM decide when retrieval is needed. Key components:

| Component                                          | File                                 | Role                                                                       |
| -------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------- |
| `Conversation` entity                              | `domain/conversation.py`             | Aggregate root owning ChatMessages; one book per conversation              |
| `ChatMessage`                                      | `domain/chat.py`                     | Has `conversation_id` (not `book_id`); roles: user, assistant, tool_result |
| `ToolDefinition`, `ToolInvocation`, `ChatResponse` | `domain/tool.py`                     | Tool-use value objects                                                     |
| `RetrievalStrategy` protocol                       | `domain/protocols.py`                | Pluggable retrieval — default: tool-use; fallback: always-retrieve         |
| `ConversationContextStrategy` protocol             | `domain/protocols.py`                | Pluggable context — default: full history capped at 20 messages            |
| `ChatWithBookUseCase`                              | `app/chat.py`                        | Agent loop orchestrator (replaces `AskBookUseCase`)                        |
| `ManageConversationsUseCase`                       | `app/conversations.py`               | Create, list, rename, delete conversations                                 |
| `chat_with_tools()`                                | `infra/llm/anthropic.py`             | Anthropic native tool-use API                                              |
| `ToolUseRetrievalStrategy`                         | `infra/retrieval/tool_use.py`        | Agent loop with max 3 iterations                                           |
| `AlwaysRetrieveStrategy`                           | `infra/retrieval/always_retrieve.py` | Ollama fallback — reformulates + always searches                           |
| `FullHistoryStrategy`                              | `infra/context/full_history.py`      | Last N messages (default 20)                                               |
| `conversation_system_prompt.md`                    | `shared/prompts/`                    | Agentic system prompt with search_book tool                                |
| `reformulation_prompt.md`                          | `shared/prompts/`                    | Query rewriting for always-retrieve strategy                               |

#### Key Decisions (already resolved — do not re-ask)

| Decision                 | Choice                                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------------------------- |
| Retrieval strategy       | Formal tool-use API (Anthropic). Pluggable `RetrievalStrategy` protocol.                                  |
| Context management       | Full conversation history in prompt, capped at 20 messages. Pluggable `ConversationContextStrategy`.      |
| Session structure        | Multiple named conversations per book. Auto-titled from first message; user can rename.                   |
| Domain entity name       | `Conversation` — NOT `Session`.                                                                           |
| ChatMessage FK           | `conversation_id` only — NO `book_id` on ChatMessage. Book reachable via `message → conversation → book`. |
| Multi-book conversations | One book per conversation for now. May evolve later.                                                      |
| Ollama tool-use          | Deferred post-MVP. Falls back to `AlwaysRetrieveStrategy`.                                                |
| Tool results visibility  | Hidden in production. Visible with `--verbose` (CLI) / debug toggle (app).                                |
| CLI command              | `cli chat <book>` — interactive REPL with conversation selection.                                         |
| Feature naming           | "Book Conversations" — ubiquitous language is "conversation", not "question" or "ask".                    |

### Swift App Architecture (Phase 10 — in progress)

The Swift app replicates the Python CLI's full pipeline in native Swift. It shares the SQL schema (`shared/schema/`), prompt templates (`shared/prompts/`), and test fixtures (`shared/fixtures/`) with the Python codebase.

#### Key Decisions (already resolved — do not re-ask)

| Decision              | Choice                                                                                                                       |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Persistence           | Raw SQLite via system C library. No ORM, no SwiftData. Shared SQL migrations are the source of truth.                        |
| Adapter naming        | Swift infra adapters use prefixed names (`SQLiteBookRepository`) unlike Python (which relies on module paths for disambiguation). This is because Swift's single-target SPM layout lacks Python's implicit namespace separation. |
| Sendability           | Repository classes are `final class` + `@unchecked Sendable`. The underlying SQLite connection is thread-safe via WAL mode.  |
| Test helpers          | `StorageTestHelper` provides in-memory DB setup and entity factory methods for storage integration tests.                    |
| SQL column constants  | Repository classes use a `private static let selectColumns` constant to avoid repeating column lists across queries.         |
| SQLiteValue helpers   | `SQLiteValue` enum has `textValue` / `integerValue` computed properties for concise optional extraction.                     |
| Platform versions     | `Package.swift` uses the highest available SPM platform enums. Will update to `.v26` when Xcode 26 GM ships.                |
| SQLite on Linux       | `CSQLite` system library target wraps `libsqlite3-dev` for Linux. Conditional dependency — Apple platforms use the native `SQLite3` framework. Use `#if canImport(SQLite3)` guard in source files. |

## First-Time Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [direnv](https://direnv.net/) — required for loading environment variables
- [SwiftLint](https://github.com/realm/SwiftLint) — Swift linter (`brew install swiftlint`)
- [SwiftFormat](https://github.com/nicklockwood/SwiftFormat) — Swift auto-formatter (`brew install swiftformat`)

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
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No | GitHub PAT for GitHub MCP server                |

### Supported Book Formats

| Format   | Extension     | Page Mapping                  | Notes                                   |
| -------- | ------------- | ----------------------------- | --------------------------------------- |
| PDF      | `.pdf`        | Document structure            | Physical page index as fallback         |
| TXT      | `.txt`        | Estimated by character count  | Labeled as "estimated page"             |
| EPUB     | `.epub`       | One page per chapter          | DRM-free only; pluggable strategy       |
| DOCX     | `.docx`       | H1 + H2 headings              | Pluggable strategy; images ignored      |
| HTML     | `.html`       | Single page (entire document) | Single file only; no linked resources   |
| Markdown | `.md`         | H1 + H2 headings              | Single file only; same strategy as DOCX |
| URL      | `http(s)://…` | Single page (fetched content) | Fetches one page; no crawling           |

Format detection: file extension for local files, HTTP Content-Type for URLs.
Page mapping is pluggable via `PageMappingStrategy` — defaults above, swappable per format.
Nested resource resolution (URL crawling, multi-file HTML/MD) is deferred to v2.
All format batches complete: Batch 1 (EPUB + DOCX) and Batch 2 (HTML + MD + URL).

### Verify Setup

After first-time setup, verify the full pipeline works:

```bash
cd python/
uv run pytest -x                                           # all tests pass
uv run ruff check .                                        # no lint errors
uv run pyright                                             # no type errors
uv run interactive-books ingest ../shared/fixtures/sample_book.pdf --title "Test"
uv run interactive-books books                             # shows the ingested book
uv run interactive-books embed <book_id>                   # requires OPENAI_API_KEY
uv run interactive-books search <book_id> "test query"     # returns ranked chunks
uv run interactive-books chat <book_id>                    # interactive conversation
```

### Swift App (Phase 10)

```bash
cd swift/InteractiveBooks/
swift build                    # build all targets
swift test                     # run tests
swift run interactive-books books   # list books from DB
swiftformat .                  # auto-format all Swift files
swiftlint lint --strict        # lint (warnings = errors)
```

The Swift package has two targets:
- `InteractiveBooksCore` (library) — Domain, Infra layers. All business logic.
- `CLI` (executable `interactive-books`) — ArgumentParser commands wired to Core.

Platform targets in `Package.swift` use the highest versions available in the current toolchain (`.iOS(.v18)`, `.macOS(.v15)`, `.visionOS(.v2)`). These will be updated to `.v26` when Xcode 26 GM ships with the corresponding SPM platform enum cases.

#### Swift Dev Tools

Dev tools are installed via **Homebrew** (not SPM plugins or Mint). They run as standalone CLI tools, not as package dependencies.

| Tool | Purpose | Install | Config |
|------|---------|---------|--------|
| **SwiftFormat** | Auto-formatter (rewrites code) | `brew install swiftformat` | `.swiftformat` |
| **SwiftLint** | Linter (catches bad patterns) | `brew install swiftlint` | `.swiftlint.yml` |

**SwiftFormat** uses standard defaults — minimal config (Swift version, indent, max width). It is authoritative for formatting. SwiftLint handles correctness rules only. When rules conflict, the SwiftLint rule is disabled (not the SwiftFormat rule).

Key SwiftFormat settings (`.swiftformat`):
- Swift 6.1, 4-space indent, 120-char max width
- All other settings use SwiftFormat defaults (`--indentcase false`, `--stripunusedargs always`, etc.)

Key SwiftLint settings (`.swiftlint.yml`) — **strict mode**:
- `--strict` in CI (warnings become errors)
- Correctness rules: `first_where`, `last_where`, `sorted_first_last`, `array_init`, `toggle_bool`, `yoda_condition`, `legacy_multiple`
- Safety rules: `force_unwrapping`, `implicitly_unwrapped_optional`, `fatal_error_message`, `unavailable_function`
- Style rules: `modifier_order`, `closure_end_indentation`, `redundant_nil_coalescing`, `redundant_type_annotation`
- Disabled rules: `trailing_comma`, `opening_brace` (owned by SwiftFormat)
- Limits: function body 25 lines (warn) / 40 (error), file 500/1000, type 300/500

**Workflow: always format before linting.**
```bash
swiftformat .              # Step 1: fix formatting
swiftlint lint --strict    # Step 2: catch real issues
```

#### CI

CI runs on `macos-15` (Xcode 16.4 + Swift 6.1.2). Don't add `setup-swift` — it's unnecessary and can cause toolchain conflicts.

CI steps: `swift build` → `swift test` → `swiftlint lint --strict` → `swiftformat --lint .`

SwiftFormat uses `--lint` mode in CI (check-only, no rewrites). Locally, run `swiftformat .` to auto-fix.

### Swift Gotchas

- **SPM basename collisions** — SPM uses file basenames for `.o` files. Two files named `BookRepository.swift` in different directories of the same target cause "multiple producers" build error. Infra files must be named after their class (`SQLiteBookRepository.swift`).
- **SQLite WAL + in-memory DBs** — `:memory:` databases silently ignore `PRAGMA journal_mode=WAL` (returns `"memory"`). Tests asserting WAL mode need a file-based temp database.
- **`nonisolated(unsafe)`** — only needed for non-`Sendable` static properties accessed across isolation domains. Don't apply it to `private` properties or types that are already safe (e.g., `NSRegularExpression` in a `let`).
- **SwiftLint vs SwiftFormat** — SwiftFormat is authoritative for formatting. When rules conflict, disable the SwiftLint rule (e.g., `trailing_comma` and `opening_brace` are disabled because SwiftFormat owns them).
- **SQLite3 on Linux** — `import SQLite3` only works on Apple platforms (system framework). On Linux, the `CSQLite` system library target bridges to `libsqlite3-dev`. Use `#if canImport(SQLite3)` / `#else import CSQLite` in any file that calls sqlite3 C functions. The dependency is conditional: `.target(name: "CSQLite", condition: .when(platforms: [.linux]))` so Apple builds are unaffected.

## Quick Commands

All Python commands run from `python/`. All Swift commands run from `swift/InteractiveBooks/`.

| Task                  | Command                              |
| --------------------- | ------------------------------------ |
| Install Python deps   | `uv sync`                            |
| Run Python tests      | `uv run pytest -x`                   |
| Run integration tests | `uv run pytest -m integration`       |
| Lint Python           | `uv run ruff check .`                |
| Format Python         | `uv run ruff format .`               |
| Type check Python     | `uv run pyright`                     |
| Run Python CLI        | `uv run interactive-books <command>` |
| Build Swift           | `swift build`                        |
| Run Swift tests       | `swift test`                         |
| Run Swift CLI         | `swift run interactive-books <cmd>`  |
| Lint Swift            | `swiftlint lint --strict`            |
| Format Swift          | `swiftformat .`                      |

### CLI Commands (current)

```bash
uv run interactive-books ingest <file|url> --title "Book Title"
uv run interactive-books embed <book_id>
uv run interactive-books search <book_id> <query> --top-k 5
uv run interactive-books chat <book_id>                  # interactive conversation REPL
uv run interactive-books books
uv run interactive-books show <book_id>
uv run interactive-books delete <book_id> --yes
uv run interactive-books set-page <book_id> <page>
```

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
- **Adapter naming (Python)** — infra adapter classes use the same name as their domain protocol. The module path provides disambiguation (e.g., `infra.parsers.pdf.BookParser` implements `domain.protocols.BookParser`). Don't encode implementation details in the class name — use the module path instead (`parsers.pdf`, not `PyMuPdfParser`). When two implementations coexist at a call site, use import aliases (`from ...pdf import BookParser as PdfBookParser`).
- **Adapter naming (Swift)** — infra adapter classes use a prefixed name (`SQLiteBookRepository`, not `BookRepository`) because Swift's single-target SPM layout lacks Python's implicit namespace packages. The prefix indicates the infrastructure technology.
- **Naming** — names reveal intent. `chunks_up_to_page(page)` not `get_filtered(p)`. Booleans read as assertions: `is_ingested`, `has_embeddings`.
- **Functions** — do one thing. If it has "and" in its description, split it. Aim for < 20 lines.
- **No empty `__init__.py`** — don't create empty `__init__.py` files. The project uses implicit namespace packages; they're unnecessary.
- **No dead code** — no commented-out code, no unused imports. Delete it; git remembers.
- **Lazy imports in CLI** — `main.py` uses function-local imports to keep startup fast. Don't use `from __future__ import annotations` in files with lazy imports — it breaks ruff's F821 name resolution. Use `TYPE_CHECKING` imports for module-level type annotations only.
- **No magic values** — `MAX_CHUNK_TOKENS = 500`, not bare `500`.
- **Dependency direction** — UI → App → Domain ← Infra. Never reverse.
- **Single level of abstraction** — high-level functions call named functions; don't mix orchestration with details.
- **Early return** — guard clauses over nested `if/else`.
- **Immutability by default** — `let` over `var` (Swift), avoid mutation where practical (Python).

## What NOT to Do

- Don't add a backend server, remote database, or web interface
- Don't target below iOS 26 / macOS 26 / visionOS 26
- Don't use Core Data or SwiftData — we use raw SQLite for schema fidelity with the shared SQL migrations
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
- Don't use `callable` (lowercase) as a type annotation — use `Callable` from `collections.abc`

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
| 3.5  | _code simplifier_  | Simplify and refine code before verification                                  |
| 4    | `/opsx:verify`     | Verify implementation matches the spec artifacts                              |
| 5    | `/opsx:archive`    | Archive the completed change                                                  |

Artifacts are stored in `openspec/changes/` during development and moved to `openspec/changes/archive/` when done.
