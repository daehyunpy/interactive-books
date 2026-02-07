# Technical Design: Interactive Books

## Architecture

```
┌────────────────────────────────────┐
│     iOS / macOS App                │
│     (SwiftUI, multiplatform)       │
│                                    │
│  ┌───────────┐  ┌───────────────┐ │
│  │Book Ingest│  │  Q&A Engine   │ │
│  │ ├─ Parser │  │  ├─ Retrieve  │ │
│  │ ├─ Chunker│  │  │  (local)   │ │
│  │ └─ Embed  │  │  └─ LLM call  │ │
│  └───────────┘  └───────────────┘ │
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

## Stack

### Python CLI

| Category        | Choice             | Notes                                            |
| --------------- | ------------------ | ------------------------------------------------ |
| Package manager | uv                 | Fast, modern                                     |
| CLI framework   | typer              | Modern, built on click                           |
| Config          | direnv + .env      | Standard, works with uv and local dev            |
| Testing         | pytest             | Standard                                         |
| Linting         | ruff               | Fast, modern                                     |

### iOS / macOS App

| Category        | Choice             | Notes                                            |
| --------------- | ------------------ | ------------------------------------------------ |
| UI framework    | SwiftUI            | Multiplatform target (iOS + macOS)               |
| Storage         | SwiftData          | Modern stack, native                             |
| Testing         | XCTest             | Standard                                         |
| Linting         | SwiftLint          | Standard                                         |

### Shared

| Category        | Choice             | Notes                                            |
| --------------- | ------------------ | ------------------------------------------------ |
| Vector search   | SQLite + sqlite-vec| Native on Apple, single DB, handles large books  |
| CI              | GitHub Actions     | Standard, free for public repos                  |

## Key Decisions

| Decision                    | Choice                         | Rationale                                                  |
| --------------------------- | ------------------------------ | ---------------------------------------------------------- |
| LLM (default)               | Anthropic (Claude)            | High quality, strong reasoning                             |
| LLM (alternatives)          | OpenAI, Ollama (local)        | User choice; local = fully offline                         |
| Embeddings                  | Independently swappable       | Chat + embedding providers configured separately           |
| Default embeddings          | Apple NaturalLanguage         | Free, offline, no second API key needed                    |
| Vector index                | SQLite + sqlite-vec           | Native on Apple, everything in one DB                      |
| App storage                 | SwiftData                     | Prefer modern stack                                        |
| CLI ↔ App data sharing     | Shared SQLite DB schema       | CLI can inspect app data; logic implemented independently  |
| Local LLM                   | Ollama first                  | Most popular. Others based on market response.             |

## Pluggable Abstractions

The project uses protocol/interface abstractions in several areas, allowing multiple implementations to coexist and be swapped:

| Abstraction       | Protocol / Base Class           | Implementations                                              |
| ----------------- | ------------------------------- | ------------------------------------------------------------ |
| **LLM Chat**      | `ChatProvider`                  | Anthropic, OpenAI, Ollama                                    |
| **Embeddings**    | `EmbeddingProvider`             | Apple NaturalLanguage, OpenAI, Voyage AI, Ollama             |
| **PDF Parser**    | `BookParser`                    | PyMuPDF, pdfplumber, pypdf (Python) / PDFKit (Swift)         |
| **Text Chunker**  | `TextChunker`                   | Recursive, sentence-based, semantic                          |
| **Keychain**      | `SecureStorage`                 | KeychainAccess, KeychainSwift, raw Security framework        |

This lets users (and developers) pick the best implementation for their needs, and makes it easy to add new ones.

## Data Flow

1. **Ingest**: Book file → parsed on-device → page boundaries mapped → chunked (500-1000 tokens, preserving page numbers) → embedded via LLM API → vectors + page metadata stored locally
2. **Query**: User question + current page position → embedded via LLM API → local vector similarity search (filtered to pages ≤ current position by default) → top-k chunks with page numbers → sent with question to LLM API → streamed response with page citations

## Page Mapping

Each chunk stores its source page number(s). This enables:
- **Page-scoped retrieval**: only search content up to the user's current page (no spoilers)
- **Page references in answers**: LLM cites specific pages in responses
- **Page-based queries**: user can ask about specific pages or page ranges
- **Tappable citations**: page references in answers link back to the chunk's source content

For PDFs, page numbers come directly from the document structure. For TXT files, pages are estimated by character/line count or user-defined page breaks.

## LLM Provider Architecture

The app uses a provider abstraction (Swift protocol / Python base class) so the RAG pipeline is provider-agnostic. Each provider implements:
- `embed(text) → vector` — generate embeddings
- `complete(prompt, context) → stream` — generate a streamed answer

### Supported Providers

| Provider         | Chat Model         | Embedding Model                   | Notes                                              |
| ---------------- | ------------------ | --------------------------------- | -------------------------------------------------- |
| Anthropic        | Claude Sonnet/Opus | Apple NaturalLanguage (default)   | Default. One API key. Embedding provider swappable. |
| OpenAI           | GPT-4o             | text-embedding-3-small            | API key required.                                  |
| Local LLM        | User's choice      | User's choice                     | Ollama (v1). Fully offline.                        |
| Apple (on-device) | —                 | NaturalLanguage framework         | Free, offline embeddings only.                     |

### Notes

- Chat provider and embedding provider are independently configurable. Any combination works.
- Anthropic defaults to Apple NaturalLanguage for embeddings (no second API key needed), but user can switch to Voyage AI, OpenAI embeddings, or Ollama at any time.
- Switching embedding provider re-indexes books (re-embeds all chunks) since vector dimensions differ across providers.
- Apple's on-device NaturalLanguage framework provides free, offline embeddings. Can be used with any chat provider to avoid embedding API costs, or paired with Ollama for a fully offline, zero-cost setup.

### Credential Storage

- iOS/macOS: API keys stored in the Keychain. Local LLM endpoint URL stored in UserDefaults.
- CLI: API keys loaded from `.env` via direnv.

## Decision Log

Resolved during planning:

- **Vector index**: SQLite + sqlite-vec — native on Apple platforms, everything in one DB.
- **On-device embeddings**: Apple NaturalLanguage framework — free, offline embedding option.
- **App storage**: SwiftData — prefer modern stack.
- **CLI ↔ App sharing**: Shared SQLite DB schema, independent code.
- **Anthropic embeddings**: Apple NaturalLanguage as default, but independently swappable.
- **Local LLM**: Ollama first. Others based on market response.
