# Phase Breakdown: iOS/macOS App

Port the full RAG pipeline to Swift and build a native SwiftUI interface for iOS 26 and macOS 26. The app shares domain semantics, database schema, and prompt templates with the Python CLI but is implemented independently in Swift.

## Overview

The iOS/macOS app is the product's primary interface. It replicates the full Python CLI pipeline — ingestion, embedding, retrieval, and agentic chat — in a native Swift codebase with a SwiftUI frontend. Everything runs on-device except LLM API calls.

### Architecture Layers

```
UI (SwiftUI)  →  App (Use Cases)  →  Domain (Entities, Protocols)  ←  Infra (Adapters)
```

### Dependencies

- Phases 1–7 (Python CLI) must be complete (they are)
- Phases 8–9 (format parsers) are independent — the Swift app can start with PDF + TXT and add formats in parallel
- Shared contracts (`shared/schema/`, `shared/prompts/`, `shared/fixtures/`) are the source of truth

---

## Sub-phase 1: Project Scaffold

Set up the Xcode project, dependencies, tooling, and directory structure.

### Tasks

1. **Create multiplatform Xcode project** — `swift/InteractiveBooks/` targeting iOS 26 + macOS 26 with a shared codebase. Use Swift Package Manager for dependencies. Single scheme for both platforms.

2. **Establish DDD directory structure** — Mirror the Python layout:
   ```
   swift/InteractiveBooks/
   ├── Package.swift (or .xcodeproj with SPM)
   ├── Sources/
   │   └── InteractiveBooks/
   │       ├── Domain/        # Entities, value objects, protocols, errors
   │       ├── App/           # Use cases
   │       ├── Infra/         # Storage, LLM, embeddings, parsers, chunkers
   │       └── UI/            # SwiftUI views, view models
   └── Tests/
       └── InteractiveBooksTests/
           ├── Domain/
           ├── App/
           └── Infra/
   ```

3. **Add SPM dependencies** — Candidates (evaluate and select):
   | Package | Purpose |
   |---------|---------|
   | EPUBKit | EPUB parsing |
   | SwiftSoup | HTML parsing |
   | swift-markdown (Apple) | Markdown parsing |
   | DocX (or raw XML) | DOCX parsing |
   | sqlite-vec | Vector search (C library, needs bridging header or SPM wrapper) |

4. **Configure SwiftLint** — Add `.swiftlint.yml` with project rules.

5. **Configure SwiftFormat** — Add `.swiftformat` config file.

6. **Add CI workflow** — GitHub Actions job for `swift build` + `swift test` on both platforms.

### Acceptance Criteria

- `swift build` succeeds for both iOS and macOS targets
- `swift test` runs (even with zero tests)
- Directory structure matches DDD conventions
- SwiftLint and SwiftFormat run without errors on empty project

---

## Sub-phase 2: Domain Layer

Port all domain entities, value objects, protocols, and errors from Python to Swift. This is a pure Swift package with zero external dependencies.

### Tasks

1. **Port domain entities** — Each as a Swift `struct` or `class` with value semantics where appropriate:

   | Python | Swift | Notes |
   |--------|-------|-------|
   | `Book` | `Book` (class, aggregate root) | `id`, `title`, `status`, `currentPage`, `embeddingProvider`, `embeddingDimension`, `createdAt`, `updatedAt`. Methods: `startIngestion()`, `completeIngestion()`, `failIngestion()`, `setCurrentPage()`, `switchEmbeddingProvider()` |
   | `BookStatus` | `BookStatus` (enum) | `.pending`, `.ingesting`, `.ready`, `.failed` |
   | `Chunk` | `Chunk` (struct, immutable) | `id`, `bookId`, `content`, `startPage`, `endPage`, `chunkIndex`, `createdAt` |
   | `Conversation` | `Conversation` (class, aggregate root) | `id`, `bookId`, `title`, `createdAt`. Methods: `rename()` |
   | `ChatMessage` | `ChatMessage` (struct, immutable) | `id`, `conversationId`, `role`, `content`, `createdAt` |
   | `MessageRole` | `MessageRole` (enum) | `.user`, `.assistant`, `.toolResult` |

2. **Port value objects** — All immutable structs:

   | Python | Swift | Notes |
   |--------|-------|-------|
   | `ChunkData` | `ChunkData` | Pre-persistence chunk data. Validated: non-empty content, page >= 1 |
   | `EmbeddingVector` | `EmbeddingVector` | `chunkId` + `vector: [Float]` |
   | `PageContent` | `PageContent` | `pageNumber` + `text`. Page >= 1 |
   | `SearchResult` | `SearchResult` | `chunkId`, `content`, `startPage`, `endPage`, `distance` |
   | `BookSummary` | `BookSummary` | Read-only projection for UI |
   | `PromptMessage` | `PromptMessage` | `role`, `content`, `toolUseId`, `toolInvocations` |
   | `ToolDefinition` | `ToolDefinition` | Tool name, description, parameter schema |
   | `ToolInvocation` | `ToolInvocation` | Tool ID, name, arguments |
   | `ChatResponse` | `ChatResponse` | `text`, `invocations`, `usage` |
   | `TokenUsage` | `TokenUsage` | `inputTokens`, `outputTokens` |
   | `ChatEvent` | `ChatEvent` (enum with associated values) | `.toolInvocation(...)`, `.toolResult(...)`, `.tokenUsage(...)` |

3. **Port domain errors** — Swift enums conforming to `Error`:

   | Python | Swift |
   |--------|-------|
   | `BookError` + `BookErrorCode` | `BookError` enum with cases: `notFound`, `parseFailed`, `unsupportedFormat`, `alreadyExists`, `drmProtected`, `fetchFailed` |
   | `LLMError` + `LLMErrorCode` | `LLMError` enum: `apiKeyMissing`, `apiCallFailed`, `rateLimited`, `timeout`, `unsupportedFeature` |
   | `StorageError` + `StorageErrorCode` | `StorageError` enum: `dbCorrupted`, `migrationFailed`, `writeFailed`, `notFound` |

4. **Define domain protocols** — Swift `protocol` definitions (dependencies point inward):

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

5. **Write unit tests** — Test all domain invariants:
   - Book status transitions
   - Validation rules (non-empty title, page >= 1, etc.)
   - Error cases
   - ChatMessage construction with correct FK
   - Conversation rename validation

### Acceptance Criteria

- All domain types compile with no dependencies on Infra or UI
- Unit tests cover all invariants from the cross-platform contracts
- Domain protocols match Python protocol signatures (adjusted for Swift conventions)
- `swift test` passes for all domain tests

---

## Sub-phase 3: Storage Layer

Implement persistence using SwiftData for relational data and sqlite-vec for vector search.

### Tasks

1. **Create SwiftData models** — `@Model` classes that map to the shared SQL schema:
   - `BookModel` → `books` table
   - `ChunkModel` → `chunks` table
   - `ConversationModel` → `conversations` table
   - `ChatMessageModel` → `chat_messages` table

   These are infra-layer models, not domain entities. Map between them in the repository implementations.

2. **Implement migration runner** — Apply migrations from `shared/schema/` in order. SwiftData auto-migration is insufficient (shared schema is plain SQL). Options:
   - Lightweight migration runner that reads `.sql` files
   - Or use raw SQLite alongside SwiftData (evaluate trade-offs)

3. **Implement `BookRepository`** — SwiftData adapter. Save/get/delete books. Map `BookModel` ↔ `Book` domain entity.

4. **Implement `ChunkRepository`** — Save chunks in batch. Query by book ID. Filter by page range (`start_page <= currentPage`). Count by book.

5. **Implement `ConversationRepository`** — CRUD operations. Order by `created_at` descending.

6. **Implement `ChatMessageRepository`** — Append-only saves. Query by conversation ID, ordered by `created_at` ascending.

7. **Integrate sqlite-vec** — Bridge the C library for vector operations:
   - Load sqlite-vec extension into the SQLite connection
   - Create virtual tables per provider/dimension: `embeddings_{providerName}_{dimension}`
   - Serialize Float arrays to binary (f32)

8. **Implement `EmbeddingRepository`** — Vector storage and search. Create tables dynamically. Batch insert. Approximate nearest neighbor search filtered by book ID.

9. **Write integration tests** — Test against a real SQLite database:
   - Book CRUD operations
   - Chunk storage and page-filtered queries
   - Conversation and message persistence
   - Vector save + search returns correct top-k
   - Migration runner applies shared schema correctly

### Key Decision: SwiftData vs Raw SQLite

SwiftData provides convenience but the shared schema is plain SQL. Options:
- **Option A**: Use SwiftData with manual schema alignment — let SwiftData manage the connection, map models carefully to match shared schema
- **Option B**: Use raw SQLite (via a thin wrapper) for full schema control — match the Python approach exactly
- **Option C**: Hybrid — SwiftData for relational data, raw SQLite for sqlite-vec virtual tables

Evaluate during implementation. The shared schema is the source of truth regardless.

### Acceptance Criteria

- All repositories implement their domain protocols
- Integration tests pass against real SQLite
- Schema matches `shared/schema/` migrations exactly
- sqlite-vec vector search returns correct results
- No SwiftData-specific types leak into the domain layer

---

## Sub-phase 4: Book Parsing

Implement format-specific parsers. Start with PDF (PDFKit), then add other formats.

### Tasks

1. **PDF parser (PDFKit)** — Native framework, no dependency:
   - Extract text page-by-page
   - Map physical page numbers (1-indexed)
   - Handle pages that fail to parse (mark as unparseable)
   - Return `[PageContent]`

2. **TXT parser** — Read file as UTF-8, divide into estimated pages by character count (default: 3000 chars/page).

3. **EPUB parser** — Evaluate EPUBKit or parse manually (EPUB is a ZIP of XHTML):
   - Extract OPF manifest for spine order and metadata (title, author)
   - Parse each chapter's XHTML → strip tags → plain text
   - One chapter = one logical page (via `PageMappingStrategy`)
   - Detect and reject DRM-protected EPUBs

4. **DOCX parser** — Evaluate DocX library or parse raw XML:
   - Extract text from paragraphs and tables
   - H1 + H2 headings define page boundaries (via `PageMappingStrategy`)
   - Ignore images and embedded objects

5. **HTML parser (SwiftSoup)** — Strip tags, extract text:
   - Single file only (no linked resources in v1)
   - Entire document = one logical page

6. **Markdown parser (swift-markdown)** — Apple's CommonMark parser:
   - Render to plain text
   - H1 + H2 headings define page boundaries (same strategy as DOCX)
   - Single file only

7. **URL fetcher (URLSession + SwiftSoup)** — Fetch + extract:
   - Fetch single URL via URLSession
   - Detect Content-Type (reject non-HTML)
   - Extract text with SwiftSoup (reuse HTML parser logic)
   - Entire fetched content = one logical page
   - Handle errors: auth required, network failure, non-text response

8. **Implement `PageMappingStrategy`** — Pluggable page mapping per format:
   - `ChapterPerPageStrategy` — one chapter = one page (EPUB)
   - `HeadingBasedStrategy` — H1 + H2 = page boundaries (DOCX, Markdown)
   - `CharCountStrategy` — character-count estimation (TXT)
   - `SinglePageStrategy` — entire document is one page (HTML, URL)

9. **Format detection** — File extension for local files, Content-Type header for URLs.

10. **Write tests** — Unit tests per parser + integration tests against `shared/fixtures/`:
    - Parse `sample_book.pdf` → verify chunk output matches `expected_chunks.json`
    - Parse `sample_book.txt`, `sample_book.epub`, `sample_book.docx`, `sample_book.html`, `sample_book.md`
    - Test error cases: missing file, empty file, DRM EPUB, unsupported format

### Build Order

Batch 1 (core): PDF + TXT (unblocks full pipeline testing)
Batch 2 (structured): EPUB + DOCX
Batch 3 (text): HTML + Markdown + URL

### Acceptance Criteria

- Each parser implements the `BookParser` protocol
- All parsers return `[PageContent]` with correct page numbering
- Cross-platform fixtures produce compatible output
- DRM EPUBs are rejected with `BookError.drmProtected`
- Unsupported formats are rejected with `BookError.unsupportedFormat`

---

## Sub-phase 5: Text Chunking

Port the recursive text chunker from Python to Swift.

### Tasks

1. **Port `TextChunker`** — Recursive splitting algorithm:
   - Default max tokens: 500, overlap: 100
   - Separator hierarchy: `"\n\n"`, `"\n"`, `". "`, `" "`
   - Build word-page pairs for page range tracking
   - Merge segments back within max_tokens
   - Add overlap (last N words of previous chunk prepended to next)

2. **Page range tracking** — Each chunk records `startPage` and `endPage` based on the pages its words came from.

3. **Write unit tests** — Verify:
   - Chunk sizes within limits
   - Overlap content matches
   - Page ranges accurate
   - Edge cases: single-page content, content shorter than max_tokens, very long pages

### Acceptance Criteria

- Chunker implements `TextChunker` protocol
- Output matches Python chunker behavior for `shared/fixtures/sample_book.pdf`
- All chunk invariants hold: non-empty content, startPage >= 1, endPage >= startPage

---

## Sub-phase 6: Embeddings

Implement embedding providers. Apple NaturalLanguage is the default (free, offline).

### Tasks

1. **Apple NaturalLanguage provider (default)** — On-device embeddings:
   - Use `NLEmbedding` for text vectorization
   - 512 dimensions
   - No API key required, fully offline
   - Batch embedding support

2. **OpenAI embedding provider** — Via URLSession:
   - Model: `text-embedding-3-small` (1536 dimensions)
   - Construct JSON request, parse JSON response
   - Retry with exponential backoff for rate limits
   - Requires `OPENAI_API_KEY`

3. **Provider abstraction** — Both implement `EmbeddingProvider` protocol with `providerName` and `dimension` properties.

4. **Write tests** — Unit tests with mocked providers. Integration test with Apple NaturalLanguage (runs on-device, no API key needed).

### Acceptance Criteria

- Apple NaturalLanguage works offline with no configuration
- OpenAI provider handles rate limits and retries
- Both return correct-dimension vectors
- Provider is independently swappable from chat provider

---

## Sub-phase 7: LLM Integration

Implement chat providers with tool-use support and streaming.

### Tasks

1. **Anthropic chat provider** — Via URLSession:
   - Model: `claude-sonnet-4-5-20250929` (or latest)
   - `chat()` — simple completion, returns `String`
   - `chatWithTools()` — tool-use support, returns `ChatResponse`
   - Convert domain `ToolDefinition` to Anthropic API schema
   - Parse response content blocks (text + tool_use)
   - Handle tool_result messages in API format
   - Streaming via `AsyncStream<String>` using SSE (Server-Sent Events)
   - Token usage extraction

2. **OpenAI chat provider** — Via URLSession:
   - Model: `gpt-4o`
   - Same protocol methods as Anthropic
   - OpenAI function calling format (different from Anthropic tool-use)
   - Streaming via SSE

3. **Ollama chat provider** — Via URLSession to local endpoint:
   - Configurable model name and base URL
   - `chat()` only (no tool-use — falls back to always-retrieve strategy)
   - Streaming support

4. **Credential storage** — API keys in Keychain:
   - `SecureStorage` protocol with Keychain adapter
   - Store/retrieve/delete API keys securely
   - Ollama endpoint URL in UserDefaults (not sensitive)

5. **Write tests** — Unit tests with mocked URLSession. Test:
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

## Sub-phase 8: Retrieval & Context

Port the retrieval strategies and context management.

### Tasks

1. **Tool-use retrieval strategy** — Port from Python:
   - Max 3 iterations in the agent loop
   - Call `chatWithTools()`, execute search on tool invocation, append tool_result, call again
   - Emit `ChatEvent` callbacks (.toolInvocation, .toolResult, .tokenUsage)
   - Format search results with `[Pages X-Y]` labels

2. **Always-retrieve fallback strategy** — For providers without tool-use:
   - Load `reformulation_prompt.md` from `shared/prompts/`
   - Reformulate user query via LLM
   - Always execute search
   - Augment user message with retrieved context
   - Call `chat()` (simple, no tools)

3. **Full history context strategy** — Port from Python:
   - Cap at last N messages (default: 20)
   - Prepend system prompt as first message
   - Preserve tool_result messages in context

4. **Prompt template loading** — Read from `shared/prompts/`:
   - `conversation_system_prompt.md` — system prompt with tool-use instructions
   - `reformulation_prompt.md` — query rewriting template
   - `query_template.md`, `citation_instructions.md`

5. **Write tests** — Unit tests with mock chat provider and search function. Test:
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
- Prompt templates loaded from shared/ directory
- Events emitted correctly during tool-use turns

---

## Sub-phase 9: Application Layer (Use Cases)

Port all use cases that orchestrate domain logic and infrastructure.

### Tasks

1. **`IngestBookUseCase`** — Parse file → chunk → save to DB → optionally embed:
   - Detect format from file extension / Content-Type
   - Select appropriate `BookParser` implementation
   - Run `TextChunker` on parsed pages
   - Save book + chunks via repositories
   - Optionally auto-embed (if embedding provider configured)
   - Update book status (pending → ingesting → ready / failed)
   - Progress callback for UI

2. **`EmbedBookUseCase`** — Batch-embed chunks and save vectors:
   - Load chunks from DB
   - Embed in batches (default: 100 per batch)
   - Save to vector DB via `EmbeddingRepository`
   - Update book embedding metadata
   - Progress callback for UI
   - Incremental: resume from last successful chunk if interrupted

3. **`SearchBooksUseCase`** — Embed query → vector search → filter by page:
   - Embed query text via `EmbeddingProvider`
   - Search via `EmbeddingRepository`
   - Join with chunk data for content and page ranges
   - Filter by `currentPage` (no spoilers)
   - Return top-k `SearchResult` objects

4. **`ChatWithBookUseCase`** — Agentic conversation orchestrator:
   - Fetch conversation, validate exists
   - Persist user message
   - Load conversation history
   - Build context via `ConversationContextStrategy`
   - Execute agent loop via `RetrievalStrategy`
   - Persist assistant response + any tool_result messages
   - Auto-title conversation on first message
   - Return response text (and streaming async sequence)

5. **`ManageConversationsUseCase`** — CRUD for conversations:
   - Create (auto-title from first message content[:60])
   - List by book (ordered by created_at DESC)
   - Rename
   - Delete (cascades to messages)

6. **`ListBooksUseCase`** — Project books to `BookSummary` for UI.

7. **`DeleteBookUseCase`** — Delete book + chunks + embeddings + conversations + messages.

8. **Write tests** — Unit tests with mocked repositories and providers for each use case.

### Acceptance Criteria

- All use cases match Python behavior
- Dependency injection via initializer (no singletons)
- Async operations use structured concurrency (async/await)
- Progress callbacks work for UI binding
- Error propagation matches error taxonomy

---

## Sub-phase 10: UI — Book Library

Build the book library screen — the app's home view.

### Tasks

1. **`BookLibraryView`** — Main screen showing all books:
   - Grid layout (default) with toggle to list layout
   - Each book shows: title, status badge, chunk count, current page
   - Pull-to-refresh
   - Empty state when no books uploaded

2. **`BookCardView`** — Individual book tile in the grid:
   - Title, status indicator (color-coded)
   - Thumbnail (placeholder or generated)
   - Tap → navigate to book detail

3. **Book import flow**:
   - **iOS**: Files picker (`.fileImporter` modifier) supporting all formats
   - **macOS**: File open dialog + drag-and-drop onto the library view
   - Show progress during ingestion
   - Handle import errors with user-friendly messages

4. **`BookDetailView`** — Detail screen for a single book:
   - Title, status, chunk count, embedding provider, dimension
   - Current reading position (editable)
   - Embed button (if not yet embedded)
   - Conversation list (navigate to chat)
   - Delete button with confirmation

5. **Search and filter** — Filter books by title. Optional: filter by status.

6. **Navigation** — `NavigationStack` with `Hashable` enum destinations:
   ```swift
   enum LibraryDestination: Hashable {
       case bookDetail(bookId: String)
       case chat(conversationId: String)
       case settings
   }
   ```

7. **View models** — `@Observable` classes that wrap use cases:
   - `BookLibraryViewModel` — loads books, handles import, delete
   - `BookDetailViewModel` — loads single book, manages reading position, triggers embedding

### Acceptance Criteria

- Library displays all books with correct metadata
- Import works on both iOS and macOS
- Ingestion progress is visible
- Navigation is declarative and type-safe
- Empty states shown when appropriate

---

## Sub-phase 11: UI — Chat Interface

Build the conversation interface — the app's core interaction.

### Tasks

1. **`ConversationListView`** — List of conversations for a book:
   - Ordered by most recent first
   - Tap to open conversation
   - Swipe to delete
   - "New Conversation" button
   - Rename via long-press or context menu

2. **`ChatView`** — The main chat interface:
   - Scrollable message list (user messages right-aligned, assistant left-aligned)
   - Tool result messages hidden by default, visible in debug mode
   - Auto-scroll to latest message
   - Message input field with send button
   - Keyboard handling (dismiss on scroll, enter to send)

3. **Streaming responses** — Display tokens as they arrive:
   - `AsyncStream<String>` from chat provider
   - Progressive text rendering in assistant bubble
   - Typing indicator while waiting for first token
   - Final message persisted when stream completes

4. **Page citations** — Tappable references in assistant messages:
   - Parse `(p.42)` and `(pp.42-43)` patterns in response text
   - Render as tappable links
   - Tap → show the source chunk's content (sheet or popover)

5. **Verbose/debug mode** — Toggle in chat view:
   - Show tool invocation details (query, top_k)
   - Show tool results (search results with page ranges)
   - Show token usage per turn
   - Implemented via `ChatEvent` callbacks

6. **Chat view model** — `@Observable` class:
   - `ChatViewModel` — wraps `ChatWithBookUseCase`, manages message list, streaming state, events
   - Handles send, new conversation, rename, delete

### Acceptance Criteria

- Multi-turn conversation works with context preserved
- Streaming displays tokens progressively
- Page citations are tappable and show source content
- Debug mode shows tool invocations and results
- Conversation persists across app restarts

---

## Sub-phase 12: UI — Settings

Build the settings screen for provider configuration and API key management.

### Tasks

1. **`SettingsView`** — App settings screen:
   - LLM provider picker: Anthropic (default), OpenAI, Ollama
   - Embedding provider picker: Apple NaturalLanguage (default), OpenAI, Ollama
   - Per-provider API key entry (SecureField)
   - Ollama endpoint URL configuration
   - Warning: switching embedding provider requires re-indexing all books

2. **Keychain integration** — `SecureStorage` protocol + Keychain adapter:
   - Store API keys securely
   - Retrieve on app launch
   - Delete when user clears settings
   - Block LLM operations when required API key is missing (show settings prompt)

3. **Provider validation** — Verify API key works:
   - Test call on save (optional, user-initiated)
   - Show clear error if key is invalid

4. **Settings view model** — `@Observable` class:
   - `SettingsViewModel` — loads/saves provider config, manages API keys via Keychain

### Acceptance Criteria

- Provider selection persists across app restarts
- API keys stored in Keychain (never in UserDefaults or on disk)
- Switching embedding provider warns about re-indexing
- Missing API key blocks operations with actionable guidance

---

## Sub-phase 13: Platform Adaptations

Handle iOS vs macOS differences in navigation, input, and layout.

### Tasks

1. **macOS sidebar navigation** — Three-column layout:
   - Sidebar: book library list
   - Content: book detail / conversation list
   - Detail: chat view

2. **iOS tab/stack navigation** — `NavigationStack` based:
   - Library → Book Detail → Chat
   - Settings accessible from tab bar or navigation bar

3. **macOS drag-and-drop** — Drop `.pdf`, `.txt`, `.epub`, `.docx`, `.html`, `.md` files onto the library view to import.

4. **iOS Files picker** — `.fileImporter` with UTType filters for supported formats.

5. **Platform-specific styling** — Adapt spacing, font sizes, and layout for each platform while sharing the core views.

6. **Keyboard shortcuts (macOS)** — Common shortcuts:
   - `Cmd+N` — new conversation
   - `Cmd+O` — import book
   - `Enter` — send message
   - `Cmd+,` — settings

### Acceptance Criteria

- macOS uses sidebar navigation pattern
- iOS uses stack navigation pattern
- Drag-and-drop works on macOS
- Files picker works on iOS
- Core views are shared; platform-specific adaptations are minimal

---

## Sub-phase 14: Integration & Polish

End-to-end testing, performance, and user experience polish.

### Tasks

1. **End-to-end flow testing** — Manual and automated:
   - Import PDF → ingest → embed → search → chat → get answer with citations
   - Test with `shared/fixtures/sample_book.pdf`
   - Verify cross-platform compatibility: Python-ingested book readable by Swift app (shared schema)

2. **Background ingestion** — Use Swift structured concurrency:
   - Ingest + embed runs in background `Task`
   - Progress indicator on book card (percentage or spinner)
   - User can browse library while ingestion runs
   - Cancellation support

3. **Error handling UI** — Surface errors with actionable messages:
   - Missing API key → navigate to settings
   - Network failure → retry button
   - Parse failure → show which pages failed
   - Rate limit → show wait time
   - Use SwiftUI `.alert()` and inline error states

4. **Loading states** — Skeleton views or spinners for:
   - Book library initial load
   - Chat message loading
   - Embedding progress
   - Search in progress

5. **Empty states** — Friendly prompts for:
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

- Full pipeline works end-to-end on both platforms
- Background processing doesn't block UI
- All error states show actionable messages
- Loading and empty states are present
- App handles 1000+ page books without degradation

---

## Dependency Graph

```
Sub-phase 1: Scaffold
    ↓
Sub-phase 2: Domain Layer
    ↓
    ├── Sub-phase 3: Storage Layer
    ├── Sub-phase 4: Book Parsing
    ├── Sub-phase 5: Text Chunking
    ├── Sub-phase 6: Embeddings
    └── Sub-phase 7: LLM Integration
            ↓
        Sub-phase 8: Retrieval & Context
            ↓
        Sub-phase 9: Application Layer
            ↓
            ├── Sub-phase 10: UI — Library
            ├── Sub-phase 11: UI — Chat
            ├── Sub-phase 12: UI — Settings
            └── Sub-phase 13: Platform Adaptations
                    ↓
                Sub-phase 14: Integration & Polish
```

Sub-phases 3–7 can be developed in parallel after the domain layer is complete. Sub-phases 10–13 can be developed in parallel after the application layer is complete.

---

## Risk Areas

| Risk | Mitigation |
|------|------------|
| **sqlite-vec Swift integration** | C library needs bridging header or SPM wrapper. Test early in Sub-phase 3. May need to vendor the C source. |
| **SwiftData vs shared SQL schema** | SwiftData auto-generates schema; shared schema is hand-written SQL. May need raw SQLite for full control. Evaluate in Sub-phase 3. |
| **EPUB/DOCX parser quality** | Swift ecosystem has fewer mature parsers than Python. EPUBKit and DocX need evaluation. May need manual XML parsing. |
| **Streaming SSE parsing** | URLSession SSE handling requires manual line parsing. No built-in SSE client in Foundation. |
| **Large book memory** | 1000+ page books need careful memory management during ingestion. Use streaming/chunked processing. |
| **Tool-use API differences** | Anthropic and OpenAI have different tool-use formats. Abstraction must handle both correctly. |

---

## Estimated Scope

| Sub-phase | Relative Size |
|-----------|--------------|
| 1. Scaffold | Small |
| 2. Domain Layer | Medium |
| 3. Storage Layer | Large (sqlite-vec integration) |
| 4. Book Parsing | Large (7 formats) |
| 5. Text Chunking | Small |
| 6. Embeddings | Medium |
| 7. LLM Integration | Large (3 providers + streaming) |
| 8. Retrieval & Context | Medium |
| 9. Application Layer | Medium |
| 10. UI — Library | Medium |
| 11. UI — Chat | Large (streaming + citations) |
| 12. UI — Settings | Small |
| 13. Platform Adaptations | Medium |
| 14. Integration & Polish | Medium |

The storage layer (sqlite-vec bridging), book parsing (7 formats), LLM integration (3 providers with streaming), and chat UI (streaming + citations) are the largest work items.
