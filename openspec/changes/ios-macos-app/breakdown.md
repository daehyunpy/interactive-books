# Phase Breakdown: iOS/macOS/visionOS App

Port the full RAG pipeline to Swift and build a native SwiftUI interface for iOS 26, macOS 26, and visionOS 2. The app shares domain semantics, database schema, and prompt templates with the Python CLI but is implemented independently in Swift.

## Overview

The iOS/macOS/visionOS app is the product's primary interface. It replicates the full Python CLI pipeline — ingestion, embedding, retrieval, and agentic chat — in a native Swift codebase with a SwiftUI frontend. Everything runs on-device except LLM API calls.

### Platform Targets

| Platform | Min Version | Status |
|----------|-------------|--------|
| iOS      | 26          | Primary target |
| iPadOS   | 26          | Primary target (shared with iOS) |
| macOS    | 26          | Primary target |
| visionOS | 2           | Supported |
| tvOS     | —           | Not supported (no keyboard, no file import) |
| watchOS  | —           | Not supported (screen/storage constraints) |

### CLI-First Approach

The Swift codebase is structured as a **Swift Package** with three targets:

```
InteractiveBooksCore   (library)   — Domain, App, Infra layers. All business logic.
interactive-books      (executable) — ArgumentParser CLI. Wires Core to terminal commands.
InteractiveBooks       (app)        — SwiftUI app. Wires Core to views and view models.
```

Build order: **Core library first, CLI second, SwiftUI app last.** Each infrastructure phase ships a working CLI command so the pipeline is validated end-to-end before any UI work begins. The CLI mirrors the Python CLI's command surface (`ingest`, `embed`, `search`, `chat`, `books`, `show`, `delete`, `set-page`).

### Architecture Layers

```
UI (SwiftUI) / CLI (ArgumentParser)  →  App (Use Cases)  →  Domain (Entities, Protocols)  ←  Infra (Adapters)
```

### Dependencies

- Phases 1–7 (Python CLI) must be complete (they are)
- Phases 8–9 (Python format parsers) are independent — the Swift app starts with PDF + TXT and adds formats later
- Shared contracts (`shared/schema/`, `shared/prompts/`, `shared/fixtures/`) are the source of truth

---

## Phase A: Project Scaffold

Set up the Swift Package, dependencies, tooling, and directory structure.

### Tasks

1. **Create Swift Package** — `swift/InteractiveBooks/Package.swift` with three targets:
   - `InteractiveBooksCore` (library) — all business logic
   - `interactive-books` (executable) — ArgumentParser CLI
   - `InteractiveBooks` (app target, added later in Phase J)
   - Platform targets: `.iOS(.v26)`, `.macOS(.v26)`, `.visionOS(.v2)`

2. **Establish DDD directory structure** — inside `Sources/InteractiveBooksCore/`:
   ```
   swift/InteractiveBooks/
   ├── Package.swift
   ├── Sources/
   │   ├── InteractiveBooksCore/
   │   │   ├── Domain/        # Entities, value objects, protocols, errors
   │   │   ├── App/           # Use cases
   │   │   └── Infra/         # Storage, LLM, embeddings, parsers, chunkers
   │   └── CLI/               # ArgumentParser commands
   └── Tests/
       └── InteractiveBooksTests/
           ├── Domain/
           ├── App/
           └── Infra/
   ```

3. **Add SPM dependencies** — initial set:
   | Package | Purpose |
   |---------|---------|
   | swift-argument-parser (Apple) | CLI framework |
   | sqlite-vec | Vector search (C library, SPM wrapper or vendored) |

   Format-specific dependencies (EPUBKit, SwiftSoup, swift-markdown, DocX) added in the phase that needs them.

4. **Configure SwiftLint** — `.swiftlint.yml` with project rules.

5. **Configure SwiftFormat** — `.swiftformat` config file.

6. **Add CI workflow** — GitHub Actions for `swift build` + `swift test`.

7. **Skeleton CLI** — `interactive-books --help` prints usage. No commands yet — just the ArgumentParser entry point and a `--version` flag.

### Acceptance Criteria

- `swift build` succeeds
- `swift test` runs (even with zero tests)
- `interactive-books --help` prints usage
- Directory structure matches DDD conventions
- SwiftLint and SwiftFormat run clean

---

## Phase B: Domain Layer

Port all domain entities, value objects, protocols, and errors from Python to Swift. Pure Swift — zero external dependencies.

### Tasks

1. **Port domain entities**:

   | Python | Swift | Notes |
   |--------|-------|-------|
   | `Book` | `Book` (class, aggregate root) | `id`, `title`, `status`, `currentPage`, `embeddingProvider`, `embeddingDimension`, `createdAt`, `updatedAt`. Methods: `startIngestion()`, `completeIngestion()`, `failIngestion()`, `setCurrentPage()`, `switchEmbeddingProvider()` |
   | `BookStatus` | `BookStatus` (enum) | `.pending`, `.ingesting`, `.ready`, `.failed` |
   | `Chunk` | `Chunk` (struct, immutable) | `id`, `bookId`, `content`, `startPage`, `endPage`, `chunkIndex`, `createdAt` |
   | `Conversation` | `Conversation` (class, aggregate root) | `id`, `bookId`, `title`, `createdAt`. Methods: `rename()` |
   | `ChatMessage` | `ChatMessage` (struct, immutable) | `id`, `conversationId`, `role`, `content`, `createdAt` |
   | `MessageRole` | `MessageRole` (enum) | `.user`, `.assistant`, `.toolResult` |

2. **Port value objects** — all immutable structs:

   | Python | Swift | Notes |
   |--------|-------|-------|
   | `ChunkData` | `ChunkData` | Pre-persistence chunk data. Validated: non-empty content, page >= 1 |
   | `EmbeddingVector` | `EmbeddingVector` | `chunkId` + `vector: [Float]` |
   | `PageContent` | `PageContent` | `pageNumber` + `text`. Page >= 1 |
   | `SearchResult` | `SearchResult` | `chunkId`, `content`, `startPage`, `endPage`, `distance` |
   | `BookSummary` | `BookSummary` | Read-only projection for UI / CLI |
   | `PromptMessage` | `PromptMessage` | `role`, `content`, `toolUseId`, `toolInvocations` |
   | `ToolDefinition` | `ToolDefinition` | Tool name, description, parameter schema |
   | `ToolInvocation` | `ToolInvocation` | Tool ID, name, arguments |
   | `ChatResponse` | `ChatResponse` | `text`, `invocations`, `usage` |
   | `TokenUsage` | `TokenUsage` | `inputTokens`, `outputTokens` |
   | `ChatEvent` | `ChatEvent` (enum with associated values) | `.toolInvocation(...)`, `.toolResult(...)`, `.tokenUsage(...)` |

3. **Port domain errors** — Swift enums conforming to `Error`:

   | Python | Swift |
   |--------|-------|
   | `BookError` + `BookErrorCode` | `BookError` enum: `notFound`, `parseFailed`, `unsupportedFormat`, `alreadyExists`, `drmProtected`, `fetchFailed` |
   | `LLMError` + `LLMErrorCode` | `LLMError` enum: `apiKeyMissing`, `apiCallFailed`, `rateLimited`, `timeout`, `unsupportedFeature` |
   | `StorageError` + `StorageErrorCode` | `StorageError` enum: `dbCorrupted`, `migrationFailed`, `writeFailed`, `notFound` |

4. **Define domain protocols**:

   | Protocol | Methods |
   |----------|---------|
   | `BookRepository` | `save(_:)`, `get(_:) -> Book?`, `getAll() -> [Book]`, `delete(_:)` |
   | `ChunkRepository` | `saveChunks(bookId:chunks:)`, `getByBook(_:) -> [Chunk]`, `getUpToPage(bookId:page:) -> [Chunk]`, `countByBook(_:) -> Int`, `deleteByBook(_:)` |
   | `ConversationRepository` | `save(_:)`, `get(_:) -> Conversation?`, `getByBook(_:) -> [Conversation]`, `delete(_:)` |
   | `ChatMessageRepository` | `save(_:)`, `getByConversation(_:) -> [ChatMessage]`, `deleteByConversation(_:)` |
   | `EmbeddingRepository` | `ensureTable(providerName:dimension:)`, `saveEmbeddings(providerName:dimension:bookId:embeddings:)`, `deleteByBook(providerName:dimension:bookId:)`, `search(providerName:dimension:bookId:queryVector:topK:) -> [(chunkId: String, distance: Float)]`, `hasEmbeddings(bookId:providerName:dimension:) -> Bool` |
   | `BookParser` | `parse(file:) async throws -> [PageContent]` |
   | `TextChunker` | `chunk(pages:) -> [ChunkData]` |
   | `ChatProvider` | `chat(messages:) async throws -> String`, `chatWithTools(messages:tools:) async throws -> ChatResponse` |
   | `EmbeddingProvider` | `embed(texts:) async throws -> [[Float]]`, `providerName: String`, `dimension: Int` |
   | `RetrievalStrategy` | `execute(chatProvider:messages:tools:searchFn:onEvent:) async throws -> (String, [ChatMessage])` |
   | `ConversationContextStrategy` | `buildContext(messages:systemPrompt:) -> [PromptMessage]` |
   | `PageMappingStrategy` | `mapPages(rawContent:) -> [PageContent]` |

5. **Write unit tests** — all domain invariants:
   - Book status transitions
   - Validation rules (non-empty title, page >= 1, etc.)
   - Error cases
   - ChatMessage construction with correct FK
   - Conversation rename validation

### Acceptance Criteria

- All domain types compile with no dependencies on Infra or UI
- Unit tests cover all invariants from the cross-platform contracts
- Domain protocols match Python protocol signatures (adjusted for Swift conventions)
- `swift test` passes

---

## Phase C: Storage Layer

Implement persistence using raw SQLite for relational data. Shared SQL schema is the source of truth.

### Tasks

1. **Thin SQLite wrapper** — lightweight connection manager around the system SQLite library. No ORM.

2. **Migration runner** — apply `.sql` files from `shared/schema/` in order. Track applied migrations in a `schema_migrations` table.

3. **Implement `BookRepository`** — SQL adapter. Map rows ↔ `Book` domain entity.

4. **Implement `ChunkRepository`** — batch insert, query by book ID, filter by page range (`start_page <= currentPage`), count by book.

5. **Implement `ConversationRepository`** — CRUD. Order by `created_at DESC`.

6. **Implement `ChatMessageRepository`** — append-only saves. Query by conversation ID, ordered by `created_at ASC`.

7. **Write integration tests** — against a real SQLite database:
   - Book CRUD
   - Chunk storage and page-filtered queries
   - Conversation and message persistence
   - Migration runner applies shared schema correctly

8. **CLI: `books` command** — `interactive-books books` lists all books (title, status, chunk count). First real command wired to the storage layer.

### Key Decision: Raw SQLite over SwiftData

The shared SQL schema is hand-written and must match exactly across Python and Swift. SwiftData auto-generates schema and fights manual control. Use raw SQLite for full schema fidelity. SwiftData is not used anywhere.

### Acceptance Criteria

- All repositories implement their domain protocols
- Integration tests pass against real SQLite
- Schema matches `shared/schema/` migrations exactly
- `interactive-books books` prints book list from the database
- No SwiftData or ORM types anywhere

---

## Phase D: sqlite-vec Integration

Bridge the sqlite-vec C library for vector storage and search. Separated from Phase C because this is the highest-risk integration point.

### Tasks

1. **Vendor or wrap sqlite-vec** — get the C library building via SPM. Options:
   - Vendor the C source with a bridging header
   - Use an SPM wrapper package
   - Evaluate trade-offs and pick the simplest path

2. **Load sqlite-vec extension** — into the SQLite connection from Phase C.

3. **Create virtual tables** — per provider/dimension: `embeddings_{providerName}_{dimension}`.

4. **Serialize Float arrays** — to f32 binary format for sqlite-vec.

5. **Implement `EmbeddingRepository`** — vector storage and approximate nearest neighbor search. Create tables dynamically. Batch insert. Search filtered by book ID.

6. **Write integration tests** — vector save + search returns correct top-k results.

### Acceptance Criteria

- sqlite-vec loads and runs inside the SQLite connection
- Vector insert + search returns correct nearest neighbors
- `EmbeddingRepository` implements the domain protocol
- Integration tests pass

---

## Phase E: Book Parsing (PDF + TXT) & Chunking

Implement the two core parsers and the text chunker. These unblock the full ingestion pipeline.

### Tasks

1. **PDF parser (PDFKit)** — native framework, no dependency:
   - Extract text page-by-page
   - Map physical page numbers (1-indexed)
   - Handle pages that fail to parse (mark as unparseable)
   - Return `[PageContent]`

2. **TXT parser** — read file as UTF-8, divide into estimated pages by character count (default: 3000 chars/page).

3. **Page mapping strategies**:
   - `CharCountStrategy` — character-count estimation (TXT)
   - Strategy interface is already in the domain protocols

4. **Port `TextChunker`** — recursive splitting algorithm:
   - Default max tokens: 500, overlap: 100
   - Separator hierarchy: `"\n\n"`, `"\n"`, `". "`, `" "`
   - Build word-page pairs for page range tracking
   - Merge segments within max_tokens
   - Add overlap (last N words of previous chunk prepended to next)

5. **Format detection** — file extension for local files.

6. **Write tests**:
   - Unit tests per parser
   - Chunker invariants (sizes within limits, overlap matches, page ranges accurate)
   - Integration tests against `shared/fixtures/sample_book.pdf` and `sample_book.txt`

7. **CLI: `ingest` command** — `interactive-books ingest <file> --title "Book Title"`. Parses, chunks, and saves to DB.

8. **CLI: `show` command** — `interactive-books show <book_id>`. Prints book details (title, status, chunk count, pages).

9. **CLI: `delete` command** — `interactive-books delete <book_id> --yes`. Deletes book + chunks + embeddings + conversations + messages.

10. **CLI: `set-page` command** — `interactive-books set-page <book_id> <page>`. Sets reading position.

### Acceptance Criteria

- Each parser implements the `BookParser` protocol
- Chunker output matches Python chunker behavior for shared fixtures
- All chunk invariants hold: non-empty content, startPage >= 1, endPage >= startPage
- `interactive-books ingest`, `show`, `delete`, `set-page` work end-to-end

---

## Phase F: Embeddings

Implement embedding providers. Apple NaturalLanguage is the default (free, offline).

### Tasks

1. **Apple NaturalLanguage provider (default)** — on-device embeddings:
   - Use `NLEmbedding` for text vectorization
   - 512 dimensions
   - No API key required, fully offline
   - Batch embedding support

2. **OpenAI embedding provider** — via URLSession:
   - Model: `text-embedding-3-small` (1536 dimensions)
   - Construct JSON request, parse JSON response
   - Retry with exponential backoff for rate limits
   - Requires `OPENAI_API_KEY`

3. **Provider abstraction** — both implement `EmbeddingProvider` protocol with `providerName` and `dimension`.

4. **Write tests** — unit tests with mocked providers. Integration test with Apple NaturalLanguage (runs on-device, no API key needed).

5. **CLI: `embed` command** — `interactive-books embed <book_id>`. Batch-embeds all chunks and saves vectors.

6. **CLI: `search` command** — `interactive-books search <book_id> <query> --top-k 5`. Embeds query, runs vector search, prints ranked results with page references.

### Acceptance Criteria

- Apple NaturalLanguage works offline with no configuration
- OpenAI provider handles rate limits and retries
- Both return correct-dimension vectors
- `interactive-books embed` and `search` work end-to-end
- Provider is independently swappable from chat provider

---

## Phase G: LLM Chat Providers

Implement chat providers with tool-use support and streaming.

### Tasks

1. **Anthropic chat provider** — via URLSession:
   - Model: `claude-sonnet-4-5-20250929` (or latest)
   - `chat()` — simple completion, returns `String`
   - `chatWithTools()` — tool-use support, returns `ChatResponse`
   - Convert domain `ToolDefinition` to Anthropic API schema
   - Parse response content blocks (text + tool_use)
   - Handle tool_result messages in API format
   - Streaming via `AsyncStream<String>` using SSE
   - Token usage extraction

2. **OpenAI chat provider** — via URLSession:
   - Model: `gpt-4o`
   - Same protocol methods as Anthropic
   - OpenAI function calling format
   - Streaming via SSE

3. **Ollama chat provider** — via URLSession to local endpoint:
   - Configurable model name and base URL
   - `chat()` only (no tool-use — falls back to always-retrieve strategy)
   - Streaming support

4. **Credential storage** — API keys in Keychain:
   - `SecureStorage` protocol with Keychain adapter
   - Store/retrieve/delete API keys securely
   - Ollama endpoint URL in UserDefaults (not sensitive)

5. **Write tests** — unit tests with mocked URLSession:
   - Request construction (headers, body format)
   - Response parsing (text, tool invocations, token usage)
   - Error handling (missing API key, network failure, rate limit)
   - Streaming event parsing

### Acceptance Criteria

- All three providers implement `ChatProvider` protocol
- Tool-use works with Anthropic and OpenAI
- Streaming delivers tokens incrementally via `AsyncStream`
- API keys stored securely in Keychain
- Provider can be switched at runtime without data loss

---

## Phase H: Retrieval & Context

Port the retrieval strategies and context management from Python.

### Tasks

1. **Tool-use retrieval strategy** — port from Python:
   - Max 3 iterations in the agent loop
   - Call `chatWithTools()`, execute search on tool invocation, append tool_result, call again
   - Emit `ChatEvent` callbacks (.toolInvocation, .toolResult, .tokenUsage)
   - Format search results with `[Pages X-Y]` labels

2. **Always-retrieve fallback strategy** — for providers without tool-use:
   - Load `reformulation_prompt.md` from `shared/prompts/`
   - Reformulate user query via LLM
   - Always execute search
   - Augment user message with retrieved context
   - Call `chat()` (simple, no tools)

3. **Full history context strategy** — port from Python:
   - Cap at last N messages (default: 20)
   - Prepend system prompt as first message
   - Preserve tool_result messages in context

4. **Prompt template loading** — read from `shared/prompts/`:
   - `conversation_system_prompt.md`
   - `reformulation_prompt.md`
   - `query_template.md`, `citation_instructions.md`

5. **Write tests** — unit tests with mock chat provider and search function:
   - Direct response (no tool use)
   - Single tool invocation → text
   - Multiple tool invocations
   - Max iteration limit reached
   - Always-retrieve reformulation flow
   - Context windowing (within limit, exceeds limit)

### Acceptance Criteria

- Both strategies implement `RetrievalStrategy` protocol
- Tool-use strategy limits iterations to prevent infinite loops
- Context strategy respects max_messages cap
- Prompt templates loaded from `shared/` directory
- Events emitted correctly during tool-use turns

---

## Phase I: Application Layer & CLI Chat

Port all use cases and wire the final CLI command — `chat`.

### Tasks

1. **`IngestBookUseCase`** — parse → chunk → save → optionally embed:
   - Detect format from file extension
   - Select appropriate `BookParser`
   - Run `TextChunker` on parsed pages
   - Save book + chunks via repositories
   - Update book status (pending → ingesting → ready / failed)
   - Progress callback

2. **`EmbedBookUseCase`** — batch-embed chunks and save vectors:
   - Load chunks from DB
   - Embed in batches (default: 100 per batch)
   - Save to vector DB via `EmbeddingRepository`
   - Update book embedding metadata
   - Progress callback
   - Incremental: resume from last successful chunk if interrupted

3. **`SearchBooksUseCase`** — embed query → vector search → filter by page:
   - Embed query text
   - Search via `EmbeddingRepository`
   - Join with chunk data for content and page ranges
   - Filter by `currentPage` (no spoilers)
   - Return top-k `SearchResult` objects

4. **`ChatWithBookUseCase`** — agentic conversation orchestrator:
   - Fetch conversation, validate exists
   - Persist user message
   - Load conversation history
   - Build context via `ConversationContextStrategy`
   - Execute agent loop via `RetrievalStrategy`
   - Persist assistant response + any tool_result messages
   - Auto-title conversation on first message
   - Return response text (and streaming async sequence)

5. **`ManageConversationsUseCase`** — CRUD:
   - Create (auto-title from first message content[:60])
   - List by book (ordered by created_at DESC)
   - Rename
   - Delete (cascades to messages)

6. **`ListBooksUseCase`** — project books to `BookSummary`.

7. **`DeleteBookUseCase`** — delete book + chunks + embeddings + conversations + messages.

8. **Wire use cases into existing CLI commands** — replace direct repository calls in `ingest`, `embed`, `search`, `delete` with use case calls.

9. **CLI: `chat` command** — `interactive-books chat <book_id>`. Interactive REPL with conversation selection, multi-turn agentic conversation, `--verbose` flag for tool result visibility.

10. **Write tests** — unit tests with mocked repositories and providers for each use case.

### Acceptance Criteria

- All use cases match Python behavior
- Dependency injection via initializer (no singletons)
- Async operations use structured concurrency
- Full CLI surface works: `ingest`, `embed`, `search`, `chat`, `books`, `show`, `delete`, `set-page`
- `interactive-books chat` produces correct agentic responses with citations

---

## Phase J: SwiftUI — Book Library

Build the book library screen. This is the first SwiftUI phase. Add the app target to `Package.swift`.

### Tasks

1. **Add app target** — `InteractiveBooks` target in `Package.swift` that depends on `InteractiveBooksCore`.

2. **`BookLibraryView`** — main screen showing all books:
   - Grid layout (default) with toggle to list layout
   - Each book shows: title, status badge, chunk count, current page
   - Pull-to-refresh
   - Empty state when no books uploaded

3. **`BookCardView`** — individual book tile:
   - Title, status indicator (color-coded)
   - Thumbnail (placeholder)
   - Tap → navigate to book detail

4. **Book import flow**:
   - **iOS / visionOS**: `.fileImporter` supporting all formats
   - **macOS**: File open dialog + drag-and-drop onto library view
   - Show progress during ingestion
   - Handle import errors with user-friendly messages

5. **`BookDetailView`** — detail screen:
   - Title, status, chunk count, embedding provider, dimension
   - Current reading position (editable)
   - Embed button (if not yet embedded)
   - Conversation list (navigate to chat)
   - Delete button with confirmation

6. **Search and filter** — filter books by title. Optional: filter by status.

7. **Navigation** — `NavigationStack` with `Hashable` enum destinations:
   ```swift
   enum LibraryDestination: Hashable {
       case bookDetail(bookId: String)
       case chat(conversationId: String)
       case settings
   }
   ```

8. **View models** — `@Observable` classes wrapping use cases:
   - `BookLibraryViewModel`
   - `BookDetailViewModel`

### Acceptance Criteria

- Library displays all books with correct metadata
- Import works on iOS, macOS, and visionOS
- Ingestion progress is visible
- Navigation is declarative and type-safe
- Empty states shown when appropriate

---

## Phase K: SwiftUI — Chat Interface

Build the conversation interface — the app's core interaction.

### Tasks

1. **`ConversationListView`** — list of conversations for a book:
   - Ordered by most recent first
   - Tap to open, swipe to delete
   - "New Conversation" button
   - Rename via long-press / context menu

2. **`ChatView`** — main chat interface:
   - Scrollable message list (user right, assistant left)
   - Tool result messages hidden by default, visible in debug mode
   - Auto-scroll to latest message
   - Message input field with send button
   - Keyboard handling

3. **Streaming responses** — tokens as they arrive:
   - `AsyncStream<String>` from chat provider
   - Progressive text rendering in assistant bubble
   - Typing indicator while waiting for first token
   - Final message persisted when stream completes

4. **Page citations** — tappable references:
   - Parse `(p.42)` and `(pp.42-43)` patterns
   - Render as tappable links
   - Tap → show source chunk content (sheet or popover)

5. **Verbose/debug mode** — toggle in chat view:
   - Tool invocation details (query, top_k)
   - Tool results (search results with page ranges)
   - Token usage per turn

6. **`ChatViewModel`** — `@Observable` class wrapping `ChatWithBookUseCase`.

### Acceptance Criteria

- Multi-turn conversation works with context preserved
- Streaming displays tokens progressively
- Page citations are tappable and show source content
- Debug mode shows tool invocations and results
- Conversation persists across app restarts

---

## Phase L: SwiftUI — Settings & Platform Adaptations

Settings screen, Keychain integration, and platform-specific navigation for iOS, macOS, and visionOS.

### Tasks

1. **`SettingsView`** — app settings:
   - LLM provider picker: Anthropic (default), OpenAI, Ollama
   - Embedding provider picker: Apple NaturalLanguage (default), OpenAI, Ollama
   - Per-provider API key entry (SecureField)
   - Ollama endpoint URL
   - Warning: switching embedding provider requires re-indexing

2. **Provider validation** — verify API key works (user-initiated test call).

3. **`SettingsViewModel`** — loads/saves provider config, manages API keys via Keychain.

4. **macOS sidebar navigation** — three-column layout:
   - Sidebar: book library list
   - Content: book detail / conversation list
   - Detail: chat view

5. **iOS stack navigation** — `NavigationStack`:
   - Library → Book Detail → Chat
   - Settings from tab bar or navigation bar

6. **visionOS navigation** — adapted from iOS stack navigation:
   - `NavigationStack` in a window
   - Library → Book Detail → Chat
   - Settings via ornament or toolbar
   - Use system-standard window sizing and placement
   - No custom volumes or immersive spaces needed — standard windowed app

7. **macOS drag-and-drop** — drop files onto library view to import.

8. **iOS Files picker** — `.fileImporter` with UTType filters.

9. **visionOS file import** — `.fileImporter` (same as iOS; visionOS supports the document picker).

10. **Keyboard shortcuts (macOS)** — `Cmd+N` (new conversation), `Cmd+O` (import), `Enter` (send), `Cmd+,` (settings).

11. **Platform-specific styling** — adapt spacing, font sizes, layout while sharing core views. Use `#if os()` conditional compilation where needed; keep platform branches minimal.

### Acceptance Criteria

- Provider selection persists across app restarts
- API keys stored in Keychain (never UserDefaults or disk)
- Switching embedding provider warns about re-indexing
- macOS uses sidebar navigation, iOS uses stack navigation
- visionOS uses windowed navigation adapted from iOS
- Drag-and-drop works on macOS, Files picker on iOS and visionOS
- Core views are shared; platform-specific code is minimal (`#if os()` branches only where necessary)

---

## Phase M: Extended Format Parsers

Add remaining format support. These parsers slot into the existing `BookParser` protocol.

### Tasks

1. **EPUB parser** — evaluate EPUBKit or parse manually (EPUB is a ZIP of XHTML):
   - Extract OPF manifest for spine order and metadata
   - Parse each chapter's XHTML → strip tags → plain text
   - One chapter = one logical page (`ChapterPerPageStrategy`)
   - Detect and reject DRM-protected EPUBs

2. **DOCX parser** — evaluate DocX library or parse raw XML:
   - Extract text from paragraphs and tables
   - H1 + H2 headings define page boundaries (`HeadingBasedStrategy`)
   - Ignore images and embedded objects

3. **HTML parser (SwiftSoup)** — strip tags, extract text:
   - Single file only (no linked resources in v1)
   - Entire document = one logical page (`SinglePageStrategy`)

4. **Markdown parser (swift-markdown)** — Apple's CommonMark parser:
   - Render to plain text
   - H1 + H2 headings define page boundaries (same strategy as DOCX)
   - Single file only

5. **URL fetcher (URLSession + SwiftSoup)** — fetch + extract:
   - Fetch single URL via URLSession
   - Detect Content-Type (reject non-HTML)
   - Extract text with SwiftSoup (reuse HTML parser logic)
   - Entire fetched content = one logical page
   - Handle errors: auth required, network failure, non-text response

6. **Page mapping strategies**:
   - `ChapterPerPageStrategy` — one chapter = one page (EPUB)
   - `HeadingBasedStrategy` — H1 + H2 = page boundaries (DOCX, Markdown)
   - `SinglePageStrategy` — entire document is one page (HTML, URL)

7. **Add SPM dependencies** — EPUBKit, SwiftSoup, swift-markdown, DocX (as needed).

8. **Update format detection** — file extension for local files, Content-Type header for URLs.

9. **Write tests** — unit tests per parser + integration tests against `shared/fixtures/`:
   - Parse each fixture, verify output
   - Error cases: missing file, empty file, DRM EPUB, unsupported format

10. **Update CLI `ingest`** — automatically selects the right parser for new formats.

### Build Order

Batch 1 (structured): EPUB + DOCX
Batch 2 (text): HTML + Markdown + URL

### Acceptance Criteria

- Each parser implements the `BookParser` protocol
- All parsers return `[PageContent]` with correct page numbering
- Cross-platform fixtures produce compatible output
- DRM EPUBs rejected with `BookError.drmProtected`
- Unsupported formats rejected with `BookError.unsupportedFormat`
- CLI `ingest` handles all formats

---

## Phase N: Integration & Polish

End-to-end testing, performance, and UX polish.

### Tasks

1. **End-to-end flow testing** — automated and manual:
   - Import PDF → ingest → embed → search → chat → answer with citations
   - Test with `shared/fixtures/sample_book.pdf`
   - Verify cross-platform compatibility: Python-ingested book readable by Swift app (shared schema)

2. **Background ingestion** — Swift structured concurrency:
   - Ingest + embed runs in background `Task`
   - Progress indicator on book card
   - User can browse library while ingestion runs
   - Cancellation support

3. **Error handling UI** — actionable messages:
   - Missing API key → navigate to settings
   - Network failure → retry button
   - Parse failure → show which pages failed
   - Rate limit → show wait time

4. **Loading states** — skeleton views or spinners for:
   - Book library initial load
   - Chat message loading
   - Embedding progress
   - Search in progress

5. **Empty states** — friendly prompts for:
   - No books uploaded
   - No conversations for a book
   - No search results
   - No embeddings yet

6. **Accessibility** — VoiceOver support:
   - Meaningful labels on all interactive elements
   - Dynamic type support
   - Sufficient contrast ratios

7. **Performance profiling** — Instruments:
   - Memory usage during large book ingestion
   - UI responsiveness during streaming
   - SQLite query performance with many chunks
   - Vector search latency

### Acceptance Criteria

- Full pipeline works end-to-end on all platforms (iOS, macOS, visionOS)
- Background processing doesn't block UI
- All error states show actionable messages
- Loading and empty states are present
- App handles 1000+ page books without degradation

---

## Dependency Graph

```
Phase A: Scaffold
    ↓
Phase B: Domain Layer
    ↓
    ├── Phase C: Storage Layer
    │       ↓
    │   Phase D: sqlite-vec Integration
    │
    ├── Phase E: Book Parsing + Chunking ──────────────────────┐
    │                                                          │
    ├── Phase F: Embeddings (needs C + D)                      │
    │                                                          │
    └── Phase G: LLM Chat Providers                            │
            ↓                                                  │
        Phase H: Retrieval & Context                           │
            ↓                                                  │
        Phase I: Application Layer & CLI Chat ◄────────────────┘
            ↓
            ├── Phase J: SwiftUI — Book Library
            ├── Phase K: SwiftUI — Chat Interface
            ├── Phase L: SwiftUI — Settings & Platform
            └── Phase M: Extended Format Parsers
                    ↓
                Phase N: Integration & Polish
```

Phases C–G can proceed in parallel after Domain (B) is complete. Phases J–M can proceed in parallel after Application (I) is complete.

---

## Risk Areas

| Risk | Mitigation |
|------|------------|
| **sqlite-vec Swift integration** | C library needs bridging header or SPM wrapper. Isolated in Phase D — test early. May need to vendor the C source. |
| **SwiftData vs shared SQL schema** | Decision made: raw SQLite, no SwiftData. Shared schema is plain SQL. |
| **EPUB/DOCX parser quality** | Swift ecosystem has fewer mature parsers. EPUBKit and DocX need evaluation. May need manual XML parsing. Deferred to Phase M. |
| **Streaming SSE parsing** | URLSession SSE handling requires manual line parsing. No built-in SSE client in Foundation. |
| **Large book memory** | 1000+ page books need streaming/chunked processing during ingestion. |
| **Tool-use API differences** | Anthropic and OpenAI have different tool-use formats. Abstraction in Phase G must handle both. |

---

## Estimated Scope

| Phase | What | Size |
|-------|------|------|
| A | Scaffold | Small |
| B | Domain Layer | Medium |
| C | Storage Layer | Medium |
| D | sqlite-vec Integration | Medium (high risk) |
| E | Book Parsing + Chunking | Medium |
| F | Embeddings | Medium |
| G | LLM Chat Providers | Large (3 providers + streaming) |
| H | Retrieval & Context | Medium |
| I | Application Layer & CLI Chat | Medium |
| J | SwiftUI — Book Library | Medium |
| K | SwiftUI — Chat Interface | Large (streaming + citations) |
| L | SwiftUI — Settings & Platform | Medium |
| M | Extended Format Parsers | Large (5 formats) |
| N | Integration & Polish | Medium |

The sqlite-vec integration (D), LLM providers (G), chat UI (K), and extended parsers (M) are the highest-effort items.
