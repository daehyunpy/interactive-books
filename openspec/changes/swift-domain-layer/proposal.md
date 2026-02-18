**Why:**
Phase A (scaffold) is complete — the Swift package builds with `InteractiveBooksCore` (library) and `interactive-books` (CLI executable) targets, DDD directory structure, swift-argument-parser dependency, and CI workflow. Before any infrastructure, parsing, or chat logic can begin, the domain layer must exist in Swift. Every subsequent phase (C through N) depends on the domain entities, value objects, protocols, and errors defined here. This is a direct port of the Python domain layer to Swift, maintaining the same semantics, invariants, and ubiquitous language across both codebases.

**What Changes:**
- Create `Domain/Entities/Book.swift` — Book class (aggregate root) with BookStatus enum, status transitions, invariant enforcement
- Create `Domain/Entities/Chunk.swift` — Chunk struct (immutable value object) with page range validation
- Create `Domain/Entities/Conversation.swift` — Conversation class (aggregate root) with rename validation
- Create `Domain/Entities/ChatMessage.swift` — ChatMessage struct with MessageRole enum
- Create `Domain/ValueObjects/ChunkData.swift` — pre-persistence chunk data with validation
- Create `Domain/ValueObjects/PageContent.swift` — page number + text with validation
- Create `Domain/ValueObjects/EmbeddingVector.swift` — chunk ID + vector with validation
- Create `Domain/ValueObjects/SearchResult.swift` — search result projection
- Create `Domain/ValueObjects/BookSummary.swift` — read-only book projection for UI/CLI
- Create `Domain/ValueObjects/PromptMessage.swift` — role + content + optional tool data
- Create `Domain/ValueObjects/ToolDefinition.swift` — tool name, description, parameter schema
- Create `Domain/ValueObjects/ToolInvocation.swift` — tool ID, name, arguments
- Create `Domain/ValueObjects/ChatResponse.swift` — text + tool invocations + usage
- Create `Domain/ValueObjects/TokenUsage.swift` — input/output token counts
- Create `Domain/ValueObjects/ChatEvent.swift` — enum with associated values for tool events
- Create `Domain/Errors/BookError.swift` — Swift enum conforming to Error
- Create `Domain/Errors/LLMError.swift` — Swift enum conforming to Error
- Create `Domain/Errors/StorageError.swift` — Swift enum conforming to Error
- Create `Domain/Protocols/` — all domain protocols (BookRepository, ChunkRepository, ConversationRepository, ChatMessageRepository, EmbeddingRepository, BookParser, TextChunker, ChatProvider, EmbeddingProvider, RetrievalStrategy, ConversationContextStrategy, PageMappingStrategy)
- Create unit tests in `Tests/InteractiveBooksTests/Domain/` for all domain invariants

**Capabilities:**

*New Capabilities:*
- `domain-models` (Swift): Domain entities (Book, Chunk, Conversation, ChatMessage) with all Python-equivalent invariants ported to Swift
- `domain-value-objects` (Swift): Immutable value objects (ChunkData, PageContent, EmbeddingVector, SearchResult, BookSummary, PromptMessage, ToolDefinition, ToolInvocation, ChatResponse, TokenUsage, ChatEvent)
- `domain-errors` (Swift): Typed error enums (BookError, LLMError, StorageError) matching the cross-platform error taxonomy
- `domain-protocols` (Swift): All domain protocols matching Python protocol signatures adjusted for Swift conventions

*Modified Capabilities:*
None — Phase A created structure only, no domain logic to modify.

**Impact:**
- **New files in `Sources/InteractiveBooksCore/Domain/`** (~20 Swift files across Entities/, ValueObjects/, Errors/, Protocols/)
- **New test files in `Tests/InteractiveBooksTests/Domain/`** (~8 test files)
- **No external dependencies** — pure Swift, zero imports from Infra or third-party packages
- **No changes to Package.swift** — InteractiveBooksCore target already includes the Domain/ directory
- **No changes to existing Phase A files**
