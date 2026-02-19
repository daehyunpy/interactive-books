**Context:**
Phase A scaffold is complete. The Swift package has `InteractiveBooksCore` (library) and `interactive-books` (CLI executable) targets with DDD directory structure (`Domain/`, `App/`, `Infra/`) and test directories mirroring the source structure. The Python domain layer (Phases 1–7) defines all entities, value objects, protocols, and errors. The app build plan (Phase B) specifies porting these 1:1 to Swift with Swift-idiomatic conventions. The technical design's cross-platform contracts (schema, error taxonomy, domain glossary) are the source of truth for both codebases.

**Goals / Non-Goals:**

*Goals:*
- Port all domain entities (Book, Chunk, Conversation, ChatMessage) with identical invariants
- Port all value objects (ChunkData, PageContent, EmbeddingVector, SearchResult, BookSummary, PromptMessage, ToolDefinition, ToolInvocation, ChatResponse, TokenUsage, ChatEvent)
- Port all domain errors (BookError, LLMError, StorageError) as Swift enums conforming to Error
- Define all domain protocols matching Python protocol signatures adjusted for Swift conventions
- Write unit tests covering all invariants using Swift Testing framework (@Test, #expect)
- Ensure zero dependencies on Infra, UI, or third-party packages

*Non-Goals:*
- No repository implementations — Phase C (Storage Layer)
- No parser implementations — Phase E (Book Parsing)
- No LLM or embedding provider implementations — Phases F–G
- No CLI commands — CLI commands are wired in their respective infrastructure phases
- No SwiftData or persistence concerns — raw SQLite comes in Phase C
- No async/await in domain types — async is only needed in infrastructure protocols

**Decisions:**

### 1. Classes for aggregate roots, structs for everything else

**Decision:** `Book` and `Conversation` are Swift `class` types (reference semantics, mutable state). All value objects (`Chunk`, `ChatMessage`, `ChunkData`, `PageContent`, etc.) are `struct` types (value semantics, immutable).

**Rationale:** Aggregate roots own mutable state (Book has status transitions, Conversation has rename). Classes provide reference semantics needed for mutation through named methods. Value objects are immutable data — structs enforce this at the language level and are cheaper to copy. This mirrors the Python pattern where `Book`/`Conversation` are mutable `@dataclass` and others use `@dataclass(frozen=True)`.

**Alternative:** All structs with `mutating` methods. Loses reference identity semantics that aggregate roots need (e.g., multiple references to the same Book should see the same state).

### 2. Swift enums for error types (not structs with code fields)

**Decision:** `BookError`, `LLMError`, and `StorageError` are Swift `enum` types conforming to `Error`, with each case corresponding to a Python error code. Associated values carry the message string.

**Rationale:** Swift enums are the idiomatic way to model error types with distinct cases. Pattern matching (`switch`/`catch`) is more natural than checking code fields. The Python model uses `DomainError(code, message)` because Python lacks tagged unions — Swift has them natively.

**Example mapping:**
```
Python: BookError(BookErrorCode.NOT_FOUND, "Book not found")
Swift:  BookError.notFound("Book not found")
```

### 3. Sendable conformance for all domain types

**Decision:** All domain types conform to `Sendable`. Structs get automatic conformance. Classes (`Book`, `Conversation`) use `@unchecked Sendable` since they are mutable aggregate roots that will be protected by actors or serial queues at the application layer.

**Rationale:** Swift 6 strict concurrency requires `Sendable` for types passed across concurrency domains. Domain types will be used in async use cases and passed between actors. Marking them `Sendable` now avoids cascading compiler errors in later phases.

**Alternative:** Make aggregate roots actors. Overkill — actors add unnecessary indirection for domain logic that doesn't do I/O. Concurrency protection belongs in the application layer.

### 4. Foundation Date for timestamps (not custom type)

**Decision:** Use `Foundation.Date` for `createdAt` and `updatedAt` fields. Provide a static `Date.now` factory (which is already the default in Foundation).

**Rationale:** `Date` is the standard Swift type for timestamps. Both SQLite (ISO 8601 strings) and SwiftUI understand it. No custom wrapper needed. Python uses `datetime` from stdlib; Swift uses `Date` from Foundation — both are standard library types.

### 5. Dictionary<String, Any> for tool parameters and arguments

**Decision:** `ToolDefinition.parameters` and `ToolInvocation.arguments` use `[String: Any]` (type-erased dictionaries), matching Python's `dict[str, object]`.

**Rationale:** Tool parameter schemas are JSON-like structures defined by the LLM API. They don't have a fixed shape at compile time. `[String: Any]` provides the flexibility needed. A `Codable`-friendly `JSONValue` enum could be added later if serialization becomes a concern, but for the domain layer it's unnecessary.

**Note:** `[String: Any]` is not `Sendable` by default. These types will use `@unchecked Sendable` since the dictionaries are immutable after construction.

### 6. ChatEvent as enum with associated values

**Decision:** `ChatEvent` is a Swift `enum` with three cases: `.toolInvocation(...)`, `.toolResult(...)`, `.tokenUsage(...)`. Each case carries the relevant data as associated values.

**Rationale:** Python uses a type union (`ToolInvocationEvent | ToolResultEvent | TokenUsageEvent`). Swift's enum with associated values is the direct equivalent and is more type-safe than a protocol-based approach. Pattern matching (`switch chatEvent`) handles all cases exhaustively.

### 7. Protocols use async throws for I/O operations

**Decision:** Protocol methods that perform I/O (`BookParser.parse`, `ChatProvider.chat`, `EmbeddingProvider.embed`, `RetrievalStrategy.execute`) are marked `async throws`. Repository protocol methods that are pure storage access are `throws` only (not async) — SQLite is synchronous.

**Rationale:** The Python codebase doesn't use async (synchronous throughout). The Swift app needs async for URLSession-based providers and non-blocking UI. Making I/O protocols async from the start avoids a painful migration later. Repository methods stay synchronous because SQLite operations are fast local I/O — wrapping them in async adds unnecessary overhead.

### 8. File organization: Entities/, ValueObjects/, Errors/, Protocols/ subdirectories

**Decision:** Organize domain files into four subdirectories under `Domain/`:
- `Entities/` — Book, Chunk, Conversation, ChatMessage (and their associated enums)
- `ValueObjects/` — ChunkData, PageContent, EmbeddingVector, SearchResult, BookSummary, PromptMessage, ToolDefinition, ToolInvocation, ChatResponse, TokenUsage, ChatEvent
- `Errors/` — BookError, LLMError, StorageError
- `Protocols/` — All domain protocols

**Rationale:** Mirrors the conceptual DDD layers within the domain. Makes it easy to verify the domain has no outward dependencies (grep Protocols/ for infrastructure imports). Each file contains exactly one public type.

### 9. Equatable and Hashable conformance

**Decision:** All domain types conform to `Equatable`. Types used as dictionary keys or in sets also conform to `Hashable`. Entity equality is by `id` only; value object equality is by all fields.

**Rationale:** `Equatable` enables testing with `#expect(a == b)`. Entity identity semantics (equal by ID) match DDD conventions. Automatic `Equatable` synthesis works for structs; classes need explicit `==` implementation comparing only `id`.

**Risks / Trade-offs:**

- **[Risk] `[String: Any]` for tool parameters is not Codable** → Acceptable: domain types don't need serialization. Infrastructure adapters handle JSON encoding/decoding when constructing API requests.

- **[Risk] `@unchecked Sendable` on mutable classes** → Acceptable: aggregate roots are mutable by design. Concurrency safety is the application layer's responsibility (e.g., actor isolation or serial dispatch queues). The alternative (making them actors) adds complexity to domain logic that doesn't do I/O.

- **[Trade-off] Foundation import in domain layer** → `Date` is the only Foundation type used. This is acceptable — Foundation is part of the Swift standard library on all Apple platforms. No third-party dependencies.

- **[Trade-off] No validation on struct init (no throwing initializer for simple value objects)** → Value objects with invariants (PageContent, ChunkData, EmbeddingVector, Chunk) use throwing initializers. Simple data carriers (SearchResult, BookSummary, TokenUsage) don't need validation.

- **[Trade-off] Protocols define async throws even though tests will use synchronous mocks** → Mock implementations can satisfy `async throws` with synchronous code (Swift allows it). This avoids two versions of each protocol.
