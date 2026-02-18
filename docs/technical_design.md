# Technical Design: Interactive Books

## Architecture

```
┌────────────────────────────────────┐
│     iOS / macOS / visionOS App     │
│     (SwiftUI, multiplatform)       │
│                                    │
│  ┌───────────┐  ┌────────────────┐│
│  │Book Ingest│  │  Chat Agent    ││
│  │ ├─ Parser │  │  ├─ Converse   ││
│  │ ├─ Chunker│  │  ├─ Retrieval  ││
│  │ └─ Embed  │  │  │  (tool)     ││
│  └───────────┘  │  └─ LLM call   ││
│                 └────────────────┘│
│                                    │
│  ┌────────────────────────────┐   │
│  │       Local Storage        │   │
│  │        SwiftData           │   │
│  └────────────────────────────┘   │
└────────────────┬───────────────────┘
                 │
                 │ HTTPS
                 ▼
         ┌───────────────┐
         │   LLM API     │
         │  (OpenAI /    │        ┌────────────────┐
         │   Anthropic)  │◄───────│  CLI (Python)  │
         └───────────────┘        │  Debug / Proto │
                                  └────────────────┘
```

## Directory Layout

```
interactive-books/
├── python/                           # Python CLI (debug/prototyping)
│   ├── pyproject.toml
│   ├── .envrc
│   ├── .env.example
│   ├── source/
│   │   └── interactive_books/
│   │       ├── __init__.py
│   │       ├── main.py              # typer app entry point
│   │       ├── domain/
│   │       │   ├── book.py          # Book aggregate root
│   │       │   ├── chunk.py         # Chunk value object
│   │       │   ├── chat.py          # ChatMessage model
│   │       │   ├── conversation.py  # Conversation aggregate
│   │       │   ├── errors.py        # BookError, LLMError, StorageError
│   │       │   └── protocols.py     # ChatProvider, EmbeddingProvider, BookParser, TextChunker
│   │       ├── app/                  # Use cases
│   │       │   ├── ingest.py
│   │       │   ├── search.py
│   │       │   └── chat.py          # ChatWithBookUseCase (agentic conversation)
│   │       └── infra/                # Adapters & external dependencies
│   │           ├── llm/
│   │           │   ├── anthropic.py
│   │           │   ├── openai.py
│   │           │   └── ollama.py
│   │           ├── embeddings/
│   │           │   ├── openai.py
│   │           │   └── ollama.py
│   │           ├── parsers/
│   │           │   ├── pdf.py
│   │           │   ├── txt.py
│   │           │   ├── epub.py
│   │           │   ├── docx.py
│   │           │   ├── html.py
│   │           │   ├── markdown.py
│   │           │   └── url.py
│   │           ├── chunkers/
│   │           │   └── recursive.py
│   │           └── storage/
│   │               ├── database.py
│   │               ├── book_repo.py
│   │               └── chunk_repo.py
│   └── tests/                        # Mirrors source/ structure
│       ├── conftest.py
│       ├── domain/
│       ├── app/
│       └── infra/
│
├── swift/                            # iOS/macOS/visionOS app (Phase 10)
│   └── InteractiveBooks/
│       ├── InteractiveBooks.xcodeproj
│       ├── Domain/
│       ├── App/
│       ├── Infra/
│       ├── UI/
│       └── Tests/
│           ├── DomainTests/
│           ├── AppTests/
│           └── InfraTests/
│
├── shared/                           # Cross-platform contracts
│   ├── schema/                       # SQL migrations (source of truth)
│   │   ├── 001_initial.sql
│   │   └── ...
│   ├── prompts/                      # Prompt templates
│   │   ├── system_prompt.md
│   │   ├── query_template.md
│   │   ├── citation_instructions.md
│   │   ├── conversation_system_prompt.md  # Agentic system prompt with tool-use instructions
│   │   └── reformulation_prompt.md        # Query reformulation from conversation context
│   └── fixtures/                     # Shared test data
│       ├── sample_book.pdf
│       ├── sample_book.txt
│       ├── expected_chunks.json
│       └── expected_schema.sql
│
├── docs/                             # Documentation only
│   ├── product_requirements.md
│   └── technical_design.md
│
├── .github/workflows/                # CI
├── openspec/                         # OpenSpec workflow
├── AGENTS.md
└── CLAUDE.md
```

### Layout Conventions

- **`python/` + `swift/`** — language-named, symmetric peers
- **`source/`** — Python src layout; `interactive_books` is the package name
- **`tests/`** — mirrors `source/` structure (separate from source, not collocated)
- **DDD layers** — `domain/`, `app/`, `infra/` in both codebases
- **Protocols in domain** — `protocols.py` defines all abstractions; dependencies point inward
- **`shared/`** — cross-platform contracts (schema, prompts, fixtures) live here, not in `docs/` or inside either codebase
- **`docs/`** — documentation only (requirements, technical design)

## Stack

### Python CLI

| Category        | Choice                      | Notes                                                                |
| --------------- | --------------------------- | -------------------------------------------------------------------- |
| Python version  | 3.13                        | Latest stable                                                        |
| Package manager | uv                          | Fast, modern                                                         |
| CLI framework   | typer                       | Modern, built on click                                               |
| Config          | pydantic-settings           | Type-safe env/config validation; direnv as dev convenience           |
| Testing         | pytest                      | Standard                                                             |
| Linting         | ruff                        | Fast, replaces black + flake8 + isort                                |
| Type checking   | pyright                     | Fast, strict, powers VS Code Pylance                                 |
| HTTP client     | httpx                       | Async + sync, HTTP/2, type-annotated                                 |
| EPUB parsing    | stdlib zipfile + selectolax | EPUB is zip of XHTML; parse OPF manifest, strip tags with selectolax |
| DOCX parsing    | python-docx                 | Extracts text from .docx paragraphs and tables                       |
| HTML parsing    | selectolax                  | Fast (Lexbor-based), modern, clean API for text extraction           |
| Markdown        | markdown-it-py              | CommonMark-compliant parser; strip to plain text                     |

### iOS / macOS App

| Category             | Choice                  | Notes                                                      |
| -------------------- | ----------------------- | ---------------------------------------------------------- |
| Min deployment       | iOS 26 / macOS 26 / visionOS 26 | Latest APIs, multiplatform SwiftUI                 |
| UI framework         | SwiftUI                 | Multiplatform target (iOS + macOS + visionOS)              |
| Storage              | SwiftData               | Modern stack, native                                       |
| Testing              | Swift Testing           | Apple's modern test framework (@Test, #expect)             |
| Linting              | SwiftLint + SwiftFormat | SwiftLint for diagnostics, SwiftFormat for auto-formatting |
| Networking           | URLSession              | Native async/await, no third-party dependency              |
| Dependency injection | Manual                  | Initializer injection + @Environment; no framework         |
| Concurrency          | Structured              | async/await, actors, AsyncStream; no GCD or Combine        |
| Navigation           | NavigationStack         | Declarative, type-safe routing via Hashable enums          |

**Swift parser candidates (evaluate during Phase 8):**

| Format   | Candidate              | Notes                                        |
| -------- | ---------------------- | -------------------------------------------- |
| PDF      | PDFKit                 | Native, already decided                      |
| EPUB     | EPUBKit                | Popular, Swift-native                        |
| DOCX     | DocX or direct XML     | No dominant Swift library; may parse raw XML |
| HTML     | SwiftSoup              | Port of Java's jsoup; well-maintained        |
| Markdown | swift-markdown (Apple) | Apple's official CommonMark parser           |
| URL      | URLSession + SwiftSoup | Fetch + extract; reuses HTML parser          |

### Shared

| Category      | Choice              | Notes                                           |
| ------------- | ------------------- | ----------------------------------------------- |
| Vector search | SQLite + sqlite-vec | Native on Apple, single DB, handles large books |
| CI            | GitHub Actions      | Standard, free for public repos                 |

## Key Decisions

| Decision                   | Choice                                     | Rationale                                                                               |
| -------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------- |
| LLM (default)              | Anthropic (Claude)                         | High quality, strong reasoning                                                          |
| LLM (alternatives)         | OpenAI, Ollama (local)                     | User choice; local = fully offline                                                      |
| Embeddings                 | Independently swappable                    | Chat + embedding providers configured separately                                        |
| Default embeddings         | Apple NaturalLanguage                      | Free, offline, no second API key needed                                                 |
| Vector index               | SQLite + sqlite-vec                        | Native on Apple, everything in one DB                                                   |
| App storage                | SwiftData                                  | Prefer modern stack                                                                     |
| CLI ↔ App data sharing    | Shared SQLite DB schema                    | CLI can inspect app data; logic implemented independently                               |
| Local LLM                  | Ollama first                               | Most popular. Others based on market response.                                          |
| Chunk size & overlap       | Pluggable (configurable)                   | Default: 500 tokens, 100 overlap. Adjustable per strategy.                              |
| Top-k retrieval            | Pluggable (configurable)                   | Default: 5. Adjustable per query.                                                       |
| Project structure          | DDD (Domain-Driven Design)                 | Clean separation of domains                                                             |
| Min deployment             | iOS 26 / macOS 26 / visionOS 26            | Latest APIs, multiplatform SwiftUI                                                      |
| Python version             | 3.13                                       | Latest stable                                                                           |
| Python config              | pydantic-settings                          | Type-safe validation; direnv as dev convenience layer                                   |
| Python type checking       | pyright                                    | Fast, strict, powers Pylance; catches bugs at dev time                                  |
| Python HTTP client         | httpx                                      | Async + sync, HTTP/2, type-annotated; replaces requests                                 |
| Swift testing              | Swift Testing                              | Apple's modern framework (@Test, #expect); no XCTest                                    |
| Swift formatting           | SwiftFormat                                | Auto-formatting complement to SwiftLint diagnostics                                     |
| Swift networking           | URLSession                                 | Native async/await; no Alamofire (Swift 6 friction)                                     |
| Swift dependency injection | Manual (initializer injection)             | Protocols + @Environment; no framework needed                                           |
| Swift concurrency          | Structured (async/await)                   | Actors, AsyncStream; no GCD or Combine                                                  |
| Agent architecture         | Tool-use with retrieval as tool            | LLM decides when/what to retrieve; pluggable `RetrievalStrategy` for alternatives       |
| Context management         | Full history (capped at N)                 | Pluggable `ConversationContextStrategy`; sliding window + summary as future alternative |
| Conversation model         | Multiple per book                          | Auto-titled from first message, user-renamable; one book per conversation for now       |
| ChatMessage FK             | `conversation_id` only                     | No `book_id` on message; book reachable via conversation                                |
| Ollama tool-use            | Deferred post-MVP                          | Falls back to always-retrieve; tool-use unreliable on local models                      |
| Tool result visibility     | Hidden in production                       | Visible in debug mode (`--verbose` / app debug toggle)                                  |
| Supported formats          | PDF, TXT, EPUB, DOCX, HTML, MD, URL        | Single-file parsing in v1; nested resource resolution deferred to v2                    |
| EPUB page mapping          | One page per chapter                       | Pluggable `PageMappingStrategy`; may subdivide long chapters in future                  |
| DOCX/MD page mapping       | H1 + H2 headings                           | Pluggable `PageMappingStrategy`; heading levels configurable in future                  |
| Format detection           | Extension for files, Content-Type for URLs | Simple and correct; URLs often lack meaningful extensions                               |
| Format build order         | Two batches                                | Batch 1: EPUB + DOCX. Batch 2: HTML + MD + URL. Natural groupings.                      |
| Swift parser libraries     | Candidates noted, not committed            | Evaluate EPUBKit, SwiftSoup, swift-markdown, etc. during Phase 8                        |

## Pluggable Abstractions

The project uses protocol/interface abstractions in several areas, allowing multiple implementations to coexist and be swapped:

| Abstraction            | Protocol / Base Class         | Implementations                                                                                                                                              |
| ---------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **LLM Chat**           | `ChatProvider`                | Anthropic, OpenAI, Ollama                                                                                                                                    |
| **Embeddings**         | `EmbeddingProvider`           | Apple NaturalLanguage, OpenAI, Voyage AI, Ollama                                                                                                             |
| **Book Parser**        | `BookParser`                  | PDF (PyMuPDF), TXT, EPUB (zipfile + selectolax), DOCX (python-docx), HTML (selectolax), Markdown (markdown-it-py), URL (httpx + selectolax) / PDFKit (Swift) |
| **Text Chunker**       | `TextChunker`                 | Recursive, sentence-based, semantic                                                                                                                          |
| **Keychain**           | `SecureStorage`               | KeychainAccess, KeychainSwift, raw Security framework                                                                                                        |
| **Retrieval Strategy** | `RetrievalStrategy`           | Tool-use (Anthropic/OpenAI), always-retrieve (fallback)                                                                                                      |
| **Context Strategy**   | `ConversationContextStrategy` | Full history (capped), sliding window + summary                                                                                                              |
| **Page Mapping**       | `PageMappingStrategy`         | Chapter-per-page (EPUB), heading-based H1+H2 (DOCX/MD), char-count (TXT), single-page (HTML/URL)                                                             |
| **Message Store**      | `ChatMessageRepository`       | SQLite                                                                                                                                                       |

This lets users (and developers) pick the best implementation for their needs, and makes it easy to add new ones.

## Embedding Dimensions

Each provider produces vectors of different sizes. The DB schema stores `embedding_provider` and `embedding_dimension` per book. Vector tables are created per book with the correct dimension at ingest time.

| Provider              | Model                  | Dimensions |
| --------------------- | ---------------------- | ---------- |
| Apple NaturalLanguage | Built-in               | 512        |
| OpenAI                | text-embedding-3-small | 1536       |
| OpenAI                | text-embedding-3-large | 3072       |
| Voyage AI             | voyage-3               | 1024       |
| Ollama                | varies by model        | 768-4096   |

Switching embedding provider re-indexes the book (re-embeds all chunks) since dimensions differ.

## Error Handling

Fail fast, surface clearly, never silently degrade.

| Layer                       | Strategy                                                             |
| --------------------------- | -------------------------------------------------------------------- |
| API key missing/invalid     | Block action, show settings screen. Don't attempt calls.             |
| API call fails (network)    | Retry once, then show error with retry button.                       |
| API call fails (rate limit) | Show "rate limited" message with wait time.                          |
| Book parsing fails          | Show which pages/sections failed. Ingest what you can, mark partial. |
| Embedding call timeout      | Resume from last successful chunk (incremental embedding).           |
| Unsupported file format     | Reject at upload with clear message listing supported formats.       |
| DRM-protected EPUB          | Reject with clear message (DRM-free only).                           |
| URL fetch fails             | Show error (network, auth required, non-HTML). Don't retry.          |
| URL returns non-text        | Reject with message explaining only text content is supported.       |
| DB corruption               | Detect on open, offer re-index from original file.                   |

Error types per domain: `BookError`, `LLMError`, `StorageError`. Swift uses `Result` type, Python uses typed exceptions. Surface errors in UI with actionable messages.

## Data Flow

1. **Ingest**: Book file (or URL) → format-specific parser extracts text and maps page/chapter boundaries → chunked (500-1000 tokens, preserving page numbers) → embedded via LLM API → vectors + page metadata stored locally
2. **Conversation turn**: User message → appended to conversation history → sent to LLM with system prompt and conversation context → LLM decides next action:
   - **Direct reply**: LLM responds from conversation context alone (no retrieval needed) → response appended to conversation history
   - **Retrieve then reply**: LLM invokes the `search_book` tool with a self-contained query (reformulated from conversation context) → query embedded via API → local vector similarity search (filtered to pages ≤ current position) → top-k chunks with page numbers → chunks returned to LLM as tool result → LLM generates response with page citations → response appended to conversation history

## Page Mapping

Each chunk stores its source page number(s). This enables:

- **Page-scoped retrieval**: only search content up to the user's current page (no spoilers)
- **Page references in answers**: LLM cites specific pages in responses
- **Page-based queries**: user can ask about specific pages or page ranges
- **Tappable citations**: page references in answers link back to the chunk's source content

Page mapping varies by format:

- **PDF**: page numbers from document structure (physical page index as fallback)
- **TXT**: estimated by character/line count; labeled as "estimated page"
- **EPUB**: chapter-based — each chapter maps to one logical page (pluggable `PageMappingStrategy`; may subdivide long chapters in future)
- **DOCX**: heading-based — H1 and H2 headings define page boundaries (pluggable `PageMappingStrategy`; heading levels configurable in future)
- **HTML**: single logical page (entire document is one page)
- **Markdown**: heading-based — H1 and H2 headings define page boundaries (same strategy as DOCX)
- **URL**: single logical page (fetched content is one page)

## LLM Provider Architecture

The app uses a provider abstraction (Swift protocol / Python base class) so the RAG pipeline is provider-agnostic. Each provider implements:

- `embed(text) → vector` — generate embeddings
- `complete(prompt, context) → stream` — generate a streamed answer

### Supported Providers

| Provider          | Chat Model         | Embedding Model                 | Notes                                               |
| ----------------- | ------------------ | ------------------------------- | --------------------------------------------------- |
| Anthropic         | Claude Sonnet/Opus | Apple NaturalLanguage (default) | Default. One API key. Embedding provider swappable. |
| OpenAI            | GPT-4o             | text-embedding-3-small          | API key required.                                   |
| Local LLM         | User's choice      | User's choice                   | Ollama (v1). Fully offline.                         |
| Apple (on-device) | —                  | NaturalLanguage framework       | Free, offline embeddings only.                      |

### Notes

- Chat provider and embedding provider are independently configurable. Any combination works.
- Anthropic defaults to Apple NaturalLanguage for embeddings (no second API key needed), but user can switch to Voyage AI, OpenAI embeddings, or Ollama at any time.
- Switching embedding provider re-indexes books (re-embeds all chunks) since vector dimensions differ across providers.
- Apple's on-device NaturalLanguage framework provides free, offline embeddings. Can be used with any chat provider to avoid embedding API costs, or paired with Ollama for a fully offline, zero-cost setup.

### Tool-Use Support

The `ChatProvider` protocol is extended to support tool-use for agentic conversation:

- `chat()` remains for simple single-turn calls (backward compatible)
- `chat_with_tools()` supports the agentic loop where the LLM can invoke tools (e.g., `search_book`)
- `ToolDefinition` is a value object describing a tool's name, description, and parameter schema
- `ChatResponse` wraps the LLM response which may contain text, tool invocations, or both

The agent loop in `ChatWithBookUseCase`:

1. Builds messages from conversation history + new user message
2. Calls `chat_with_tools()` with the `search_book` tool definition
3. If LLM returns a tool invocation: executes the search, appends results as a `tool_result` message, calls LLM again
4. If LLM returns text: returns the response and persists the conversation turn

`tool_result` messages are persisted in conversation history but hidden from users by default. They are visible in debug mode (`--verbose` in CLI, debug toggle in app).

Providers that don't support tool-use (Ollama, for now) fall back to always-retrieve behavior via the `RetrievalStrategy` abstraction. This is a known limitation to be addressed post-MVP.

### Credential Storage

- iOS/macOS/visionOS: API keys stored in the Keychain. Local LLM endpoint URL stored in UserDefaults.
- CLI: API keys loaded from `.env` via pydantic-settings (direnv as dev convenience).

## Build Order

CLI first, bottom-up, one feature at a time.

| Phase | What                          | Details                                                                                                                                                             |
| ----- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | **Project scaffold**          | Monorepo structure (DDD), `pyproject.toml`, `.envrc`, CI skeleton                                                                                                   |
| 2     | **DB schema**                 | SQLite schema + migrations, shared between CLI and app                                                                                                              |
| 3     | **Book ingestion**            | PDF parser → chunker → page mapping                                                                                                                                 |
| 4     | **Embeddings**                | Embed chunks → store in sqlite-vec                                                                                                                                  |
| 5     | **Retrieval**                 | Vector search with page filtering                                                                                                                                   |
| 6     | **Q&A (Agentic Chat)**        | Conversation sessions + agent loop with tool-use: LLM decides when to retrieve, reformulates queries from conversation context, streams answers with page citations |
| 7     | **CLI polish**                | All commands working (`ingest`, `search`, `chat`, `books`, `--verbose`)                                                                                             |
| 8     | **Structured format parsers** | EPUB (zipfile + selectolax) + DOCX (python-docx) parsers with `PageMappingStrategy`, sample fixtures, integration tests                                             |
| 9     | **Text format parsers**       | HTML (selectolax) + Markdown (markdown-it-py) + URL (httpx + selectolax) parsers, Content-Type detection for URLs, sample fixtures, integration tests               |
| 10    | **iOS/macOS/visionOS app**    | Port pipeline to Swift, build SwiftUI interface                                                                                                                     |

## First Implementations (Easiest First)

For each pluggable abstraction, start with the simplest implementation:

| Abstraction        | First Implementation        | Why easiest                                                               |
| ------------------ | --------------------------- | ------------------------------------------------------------------------- |
| Book Parser (PDF)  | PyMuPDF                     | Fast, simple API, good page extraction                                    |
| Book Parser (EPUB) | stdlib zipfile + selectolax | Parse OPF for spine order, strip XHTML tags; zero new EPUB dep            |
| Book Parser (DOCX) | python-docx                 | Simple paragraph/table text extraction                                    |
| Book Parser (HTML) | selectolax                  | Fast Lexbor-based parser, clean text extraction API                       |
| Book Parser (MD)   | markdown-it-py              | CommonMark-compliant, strip to plain text                                 |
| Book Parser (URL)  | httpx + selectolax          | Fetch + extract; reuses HTML parser                                       |
| Page Mapping       | Per-format defaults         | Chapter (EPUB), H1+H2 (DOCX/MD), char-count (TXT), single-page (HTML/URL) |
| Text Chunker       | Recursive                   | Split by `\n\n` → `\n` → sentence, ~100 lines                             |
| Embeddings         | OpenAI                      | Simplest SDK, one-line call                                               |
| Chat               | Anthropic                   | Default provider, good SDK                                                |
| Keychain           | KeychainAccess              | One-liner API                                                             |
| Retrieval Strategy | Tool-use (Anthropic/OpenAI) | Native API support, structured input/output                               |
| Context Strategy   | Full history (capped)       | Simplest; sufficient for MVP                                              |

Additional implementations are added after the first end-to-end pipeline works.

## Cross-Platform Contracts

The Python CLI and Swift app are implemented independently but share a database and domain model. These contracts prevent drift between the two codebases.

### Schema Source of Truth

One set of SQL migration files that both codebases reference. Neither side invents schema independently.

```
shared/schema/
  001_initial.sql
  002_add_embeddings.sql
  ...
```

- Migrations are numbered sequentially. Both sides apply them in order.
- Each migration file is plain SQL — no ORM-specific syntax.
- The CLI applies migrations via raw SQL. The app applies them via a lightweight migration runner (not SwiftData auto-migration).
- Adding a column, table, or index always starts with a new migration file here, then both sides implement support.

The agentic chat system requires a schema update to add a `conversations` table (`id`, `book_id`, `title`, `created_at`) and replace the `book_id` foreign key on `chat_messages` with a `conversation_id` foreign key. Since neither the `ChatMessage` model nor the `chat_messages` table are in use yet, this can be folded into `001_initial.sql` or added as a new migration — implementation decision.

### Domain Glossary

Canonical names for shared concepts. Python uses `snake_case`, Swift uses `camelCase`, but the **base name** is identical.

| Concept                  | DB column             | Python                     | Swift                     |
| ------------------------ | --------------------- | -------------------------- | ------------------------- |
| Book identity            | `id`                  | `book.id`                  | `book.id`                 |
| Book title               | `title`               | `book.title`               | `book.title`              |
| Chunk text content       | `content`             | `chunk.content`            | `chunk.content`           |
| Chunk start page         | `start_page`          | `chunk.start_page`         | `chunk.startPage`         |
| Chunk end page           | `end_page`            | `chunk.end_page`           | `chunk.endPage`           |
| Embedding provider name  | `embedding_provider`  | `book.embedding_provider`  | `book.embeddingProvider`  |
| Embedding dimensions     | `embedding_dimension` | `book.embedding_dimension` | `book.embeddingDimension` |
| Ingestion status         | `status`              | `book.status`              | `book.status`             |
| Current reading page     | `current_page`        | `book.current_page`        | `book.currentPage`        |
| Conversation identity    | `id`                  | `conversation.id`          | `conversation.id`         |
| Conversation book ref    | `book_id`             | `conversation.book_id`     | `conversation.bookId`     |
| Conversation title       | `title`               | `conversation.title`       | `conversation.title`      |
| Conversation created     | `created_at`          | `conversation.created_at`  | `conversation.createdAt`  |
| Message conversation ref | `conversation_id`     | `message.conversation_id`  | `message.conversationId`  |
| Chat message role        | `role`                | `message.role`             | `message.role`            |
| Chat message content     | `content`             | `message.content`          | `message.content`         |

If a new domain concept is added, add it to this table first, then implement in both codebases.

> **Note:** `ChatMessage` references `Conversation` (via `conversation_id`), not `Book` directly. The book is reachable via `message → conversation → book`. Multi-book conversations may be considered in a future iteration.

### Domain Invariants

Rules that both implementations must enforce identically:

- A `Book` must have a non-empty `title`
- A `Book`'s `status` is one of: `pending`, `ingesting`, `ready`, `failed`
- A `Chunk` always has `start_page >= 1` and `end_page >= start_page`
- A `Chunk` always belongs to exactly one `Book`
- `current_page` defaults to `0` (meaning "no position set" — retrieval returns all pages)
- When `current_page > 0`, retrieval only returns chunks where `start_page <= current_page`
- Deleting a `Book` cascades to its chunks, embeddings, conversations, and messages
- Switching embedding provider sets `status` back to `pending` (requires re-indexing)
- A `Conversation` always belongs to exactly one `Book`
- A `Conversation` has a non-empty `title` (auto-generated from first message, user-renamable)
- A `ChatMessage` belongs to one `Conversation` (via `conversation_id`; no direct `book_id`)
- Messages within a conversation are ordered by `created_at`
- Deleting a `Conversation` cascades to its messages
- The agent sends at most the last N messages as conversation context to the LLM (configurable; default TBD during implementation)

### Error Taxonomy

Both codebases use the same error categories with equivalent cases:

| Domain  | Python         | Swift          | Cases                                                                                                |
| ------- | -------------- | -------------- | ---------------------------------------------------------------------------------------------------- |
| Book    | `BookError`    | `BookError`    | `not_found`, `parse_failed`, `unsupported_format`, `already_exists`, `drm_protected`, `fetch_failed` |
| LLM     | `LLMError`     | `LLMError`     | `api_key_missing`, `api_call_failed`, `rate_limited`, `timeout`, `unsupported_feature`               |
| Storage | `StorageError` | `StorageError` | `db_corrupted`, `migration_failed`, `write_failed`, `not_found`                                      |

Python uses `snake_case` enum values; Swift uses `camelCase`. The semantic meaning is identical.

> **Note:** The `chat_messages.role` column constraint must include `'tool_result'` in addition to `'user'` and `'assistant'` to support persisted tool invocation results in conversation history.

### Prompt Templates

System prompts and prompt construction are documented in a shared location so both implementations produce equivalent LLM inputs.

```
shared/prompts/
  system_prompt.md                  — base system prompt for single-turn Q&A
  query_template.md                 — how retrieved chunks + user question are assembled
  citation_instructions.md          — how to instruct the LLM to cite pages
  conversation_system_prompt.md     — agentic system prompt with tool-use instructions
  reformulation_prompt.md           — instructions for resolving anaphora and producing
                                       a self-contained search query
```

Changes to prompt wording go through these files first, then both sides update their implementation.

### Shared Test Fixtures

A set of known-good test data that both codebases test against to verify compatibility:

```
shared/fixtures/
  sample_book.pdf         — a small PDF for ingestion testing
  sample_book.txt         — a plain text book
  sample_book.epub        — a small EPUB for ingestion testing
  sample_book.docx        — a small DOCX for ingestion testing
  sample_book.html        — a single-page HTML for ingestion testing
  sample_book.md          — a Markdown file for ingestion testing
  expected_chunks.json    — expected chunking output for sample_book.pdf
  expected_schema.sql     — current schema snapshot for validation
```

Both sides include integration tests that ingest `sample_book.pdf` and verify the resulting chunks match `expected_chunks.json`. This catches drift in parsing, chunking, or page mapping between the two implementations.
