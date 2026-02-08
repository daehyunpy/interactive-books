# AGENTS.md

Instructions for AI agents working on this codebase.

## Project

Interactive Books — a local-only iOS/macOS app for uploading books and chatting about them using RAG. No backend server.

## Key Docs

- `docs/product_requirements.md` — what to build and why
- `docs/technical_design.md` — how to build it (architecture, stack, decisions)

Read both before making changes.

## Architecture

- **iOS / macOS app**: SwiftUI multiplatform, SwiftData, iOS 26 / macOS 26
- **Python CLI**: debug/prototyping tool, Python 3.13, uv, typer
- **Shared**: SQLite + sqlite-vec for vector search, shared DB schema between CLI and app
- **No backend server**. Only outbound calls are to LLM APIs.

## Project Structure

DDD (Domain-Driven Design). Code is organized by domain, not by layer.

## Coding Style

This project follows three disciplines: **DDD**, **TDD**, and **Clean Code**. These are not just project structure conventions — they govern how every line of code is written.

### DDD (Domain-Driven Design)

Beyond folder layout, DDD shapes how we model and name things:

- **Ubiquitous language** — use domain terms consistently in code, tests, docs, and conversation. A `Book` is a `Book`, not a `Document` or `Item`. A `Chunk` is a `Chunk`, not a `Segment` or `Fragment`. If the domain term changes, rename everywhere.
- **Entities vs Value Objects** — entities have identity (`Book` has an ID, persists, tracks state). Value objects are immutable data with no identity (`PageRange`, `ChunkMetadata`, `EmbeddingVector`). Don't give value objects IDs. Don't make entities mutable where a value object suffices.
- **Aggregates** — each aggregate has a single root that controls access. `Book` is an aggregate root — access its `Chunk`s through `Book`, not independently. Don't let outside code reach into aggregate internals.
- **Domain logic belongs in domain objects** — not in controllers, CLI handlers, or UI code. If you're writing an `if` statement about book state in a command handler, it belongs in the domain layer.
- **Domain layer has no outward dependencies** — domain code never imports infrastructure (DB, API clients, file I/O). It depends only on protocols/interfaces. Infrastructure adapts to the domain, not the other way around.
- **Domain errors** — use `BookError`, `LLMError`, `StorageError`. Don't catch domain errors in the domain layer; let them propagate to the application layer.

### TDD (Test-Driven Development)

Write tests first, not after:

- **Red → Green → Refactor** — write a failing test, make it pass with the simplest code, then refactor. Every feature and bug fix starts with a test.
- **Test naming** — test names describe behavior, not implementation: `test_search_excludes_chunks_beyond_current_page`, not `test_search_method`.
- **Test structure** — follow Arrange-Act-Assert (Python) / Given-When-Then (Swift). One assertion per test where practical.
- **Test boundaries**:
  - **Unit tests** — test domain logic in isolation. Mock infrastructure (DB, API). These run fast and cover edge cases.
  - **Integration tests** — test that infrastructure adapters (SQLite, API clients) work correctly. Use real dependencies.
  - **No test for trivial code** — don't test getters, data classes, or framework glue.
- **Test location** — tests live alongside the code they test, not in a separate top-level `tests/` tree. Each domain module has its own tests.
- **Protocols enable testing** — every protocol (`ChatProvider`, `BookParser`, etc.) should have a test double. This is why we use protocols — to make domain logic testable without real infrastructure.

### Clean Code

Write code that reads like well-written prose:

- **Naming** — names reveal intent. `chunks_up_to_page(page)` not `get_filtered(p)`. No abbreviations except widely known ones (`db`, `url`, `id`). Boolean names read as assertions: `is_ingested`, `has_embeddings`.
- **Functions** — do one thing. If a function has "and" in its description, split it. Keep them short — aim for < 20 lines. Extract when logic deserves a name, not to hit a line count.
- **No dead code** — no commented-out code, no unused imports, no "just in case" parameters. Delete it; git remembers.
- **No magic values** — use named constants or enums. `MAX_CHUNK_TOKENS = 500`, not bare `500`.
- **Dependency direction** — always point inward. UI → Application → Domain ← Infrastructure. Never reverse this. The domain layer is the center; everything else adapts to it.
- **Single level of abstraction** — each function operates at one level. A high-level function calls other named functions; it doesn't mix orchestration with implementation details.
- **Early return** — prefer guard clauses over nested `if/else`. Reduce indentation.
- **Immutability by default** — use `let` over `var` (Swift), avoid mutation where practical (Python). Mutable state is the exception, not the rule.

## Conventions

### Python (CLI)

- Package manager: `uv`
- Linting + formatting: `ruff`
- Type checking: `pyright`
- Testing: `pytest`
- HTTP client: `httpx`
- Config: `pydantic-settings` (type-safe validation; `direnv` as dev convenience)
- Python 3.13 — use modern syntax (type unions with `|`, etc.)

### Swift (App)

- SwiftUI with multiplatform target
- SwiftData for persistence
- SwiftLint for diagnostics + SwiftFormat for auto-formatting
- Swift Testing for all tests (`@Test`, `#expect`)
- Networking: URLSession with async/await (no Alamofire)
- Dependency injection: manual initializer injection + `@Environment` (no framework)
- Concurrency: structured concurrency — `async/await`, `actor`, `AsyncStream` (no GCD, no Combine)
- Navigation: `NavigationStack` with type-safe routing
- Min deployment: iOS 26 / macOS 26 — use latest APIs freely

### Both

- SQLite + sqlite-vec for vector storage
- Shared DB schema between CLI and app
- CI: GitHub Actions

## Cross-Platform Contracts

The Python CLI and Swift app are independent codebases that share a database and domain model. To prevent drift:

- **Schema**: single source of truth in `docs/schema/` — numbered SQL migrations, both sides apply them
- **Domain glossary**: canonical names in `docs/technical_design.md` — same base names, language-appropriate casing
- **Domain invariants**: shared rules (e.g., "a Chunk always has `start_page >= 1`") documented once, enforced in both
- **Error taxonomy**: same error types and cases (`BookError`, `LLMError`, `StorageError`) in both codebases
- **Prompt templates**: shared in `docs/prompts/` — both sides produce equivalent LLM inputs
- **Test fixtures**: shared in `tests/fixtures/` — both sides verify identical output from the same input

When adding a new DB column, domain concept, error case, or prompt change: update the shared contract first, then implement in both codebases.

See `docs/technical_design.md` → "Cross-Platform Contracts" for full details.

## Pluggable Abstractions

The project uses protocol/interface patterns. When adding new functionality, check if it fits an existing abstraction:

| Abstraction    | Protocol          | Add implementations, don't modify the protocol unless necessary |
| -------------- | ----------------- | --------------------------------------------------------------- |
| LLM Chat       | `ChatProvider`    | Anthropic, OpenAI, Ollama                                       |
| Embeddings     | `EmbeddingProvider`| Apple NaturalLanguage, OpenAI, Voyage AI, Ollama               |
| PDF Parser     | `BookParser`      | PyMuPDF, pdfplumber, pypdf (Python) / PDFKit (Swift)            |
| Text Chunker   | `TextChunker`     | Recursive, sentence-based, semantic                             |
| Keychain       | `SecureStorage`   | KeychainAccess, KeychainSwift, raw Security framework           |

## Error Handling

- Fail fast, surface clearly, never silently degrade
- Use domain-typed errors: `BookError`, `LLMError`, `StorageError`
- Swift: `Result` type. Python: typed exceptions.
- Always provide actionable error messages

## Key Design Principles

1. **Local-only** — no backend, no cloud storage, no accounts
2. **Page-aware** — every chunk tracks page numbers; retrieval respects reading position to avoid spoilers
3. **Pluggable** — providers, parsers, chunkers, and storage are all swappable via protocols
4. **Chat + embedding providers are independent** — any combination works
5. **Easiest first** — start with the simplest implementation of each abstraction, add complexity later

## What NOT to Do

- Don't add a backend server or remote database
- Don't hardcode a single LLM provider — always go through the abstraction
- Don't mix domain logic across boundaries (DDD)
- Don't add web interface code
- Don't target below iOS 26 / macOS 26
- Don't use Core Data — we use SwiftData
- Don't write code without a failing test first (TDD)
- Don't put domain logic in infrastructure or UI layers
- Don't let domain code import infrastructure modules
- Don't leave dead code, commented-out code, or unused imports
- Don't use magic numbers or strings — name them
- Don't add DB columns, domain concepts, or error cases without updating the shared contracts first
- Don't change prompt templates in one codebase without updating `docs/prompts/`

## Build Order

We're building CLI first, then the app. See `docs/technical_design.md` for the 8-phase plan.

## OpenSpec

This project uses OpenSpec for spec-driven development. Changes go through:
`/opsx:new` → `/opsx:ff` → `/opsx:apply` → `/opsx:verify` → `/opsx:archive`
