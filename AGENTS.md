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

## Conventions

### Python (CLI)

- Package manager: `uv`
- Linting: `ruff`
- Testing: `pytest`
- Config: `direnv` + `.env` for API keys
- Python 3.13 — use modern syntax (type unions with `|`, etc.)

### Swift (App)

- SwiftUI with multiplatform target
- SwiftData for persistence
- SwiftLint for linting
- XCTest for testing
- Min deployment: iOS 26 / macOS 26 — use latest APIs freely

### Both

- SQLite + sqlite-vec for vector storage
- Shared DB schema between CLI and app
- CI: GitHub Actions

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

## Build Order

We're building CLI first, then the app. See `docs/technical_design.md` for the 8-phase plan.

## OpenSpec

This project uses OpenSpec for spec-driven development. Changes go through:
`/opsx:new` → `/opsx:ff` → `/opsx:apply` → `/opsx:verify` → `/opsx:archive`
