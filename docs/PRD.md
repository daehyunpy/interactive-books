# Product Requirement Document: Interactive Books

## Overview

A local-only iOS and macOS app that lets users upload books and have conversations about them. All processing happens on-device or via direct API calls to an LLM provider — no backend server required. Users can ask questions, get summaries, find specific passages, and explore themes using RAG (retrieval-augmented generation).

A Python CLI tool is provided for debugging and rapid prototyping of the RAG pipeline.

## Problem

Reading a book and retaining or finding specific information is time-consuming. Readers often want to:
- Quickly recall details from a book they've read
- Get summaries of chapters or sections
- Ask analytical questions ("What motivates character X?")
- Find specific passages without manually searching

## Target User

Individual readers who want a faster way to interact with and extract value from books they own.

## Platforms

- **iOS** — native app (Swift/SwiftUI), all data stored on-device
- **macOS** — native app (Swift/SwiftUI), shared codebase with iOS via multiplatform target
- **CLI** — Python command-line tool for debugging and quick prototyping

No backend server. No web interface.

## Core Features

### P0 — Must Have

1. **Book Upload**
   - Users can upload book files (PDF, TXT)
   - App parses, chunks, and indexes content locally
   - iOS: upload from Files picker
   - macOS: upload via file open dialog or drag-and-drop onto window

2. **Ask Questions**
   - Chat-style interface for asking questions about a book
   - App retrieves relevant passages locally, sends them with the question to an LLM API
   - Answers include references to the source passages
   - Streaming responses for real-time feel

3. **Book Library**
   - Grid/list view of uploaded books
   - Users can select which book to chat about
   - Search and filter books

4. **LLM Provider Selection**
   - User chooses their LLM provider in settings:
     - **Anthropic (Claude)** — default provider
     - **OpenAI (GPT)**
     - **Local LLM** — connect to a locally running model (e.g. Ollama, llama.cpp server)
   - API key stored in Keychain (Anthropic / OpenAI)
   - Local LLM: user configures endpoint URL (e.g. `http://localhost:11434`)
   - Provider can be switched at any time; existing books and chat history are preserved

### P1 — Should Have

5. **Large Book Support (1000+ pages)**
   - Efficient chunking and indexing for very large books
   - On-disk vector index (not purely in-memory) to handle large embedding sets
   - Background ingestion with progress indicator
   - Incremental embedding (resume if interrupted)

6. **Chapter Summaries**
   - Users can request a summary of a specific chapter or section
   - App identifies chapter boundaries and summarizes content

7. **Multi-Book Queries**
   - Users can ask questions across multiple books at once
   - Useful for comparing themes, characters, or ideas across works

8. **Chat History**
   - Conversation history is persisted locally per book
   - Users can revisit prior Q&A sessions

### P2 — Nice to Have

9. **EPUB Support**
   - Support for EPUB format in addition to PDF and TXT

10. **Highlights & Notes**
    - Users can save interesting passages or answers
    - Export notes as markdown

10. **iCloud Sync**
    - Sync book metadata and chat history across iOS and macOS via iCloud
    - Book content stays on-device (too large for sync)

## CLI Tool (Debug / Prototyping)

A Python CLI for debugging and rapid prototyping. Used to iterate on the RAG pipeline quickly before implementing in Swift.

### Commands

- `cli ingest <file>` — parse, chunk, embed a book and inspect the results
- `cli search <book> <query>` — run vector search and see retrieved chunks with similarity scores
- `cli ask <book> <question>` — full end-to-end question answering
- `cli books` — list ingested books, chunk counts, metadata
- `--verbose` flag — log chunk boundaries, similarity scores, prompt construction, token counts

### Role

The CLI serves two purposes:
1. **Prototyping** — quickly test different chunking strategies, embedding models, prompt templates, and retrieval parameters without rebuilding an Xcode project
2. **Debugging** — inspect intermediate pipeline state (chunks, embeddings, retrieved context, final prompt) when something isn't working

The CLI is not a user-facing product.

## Technical Approach

### Architecture

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
│  │    Core Data / SwiftData   │   │
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

### Key Technical Decisions

| Decision       | Choice                  | Rationale                                        |
| -------------- | ----------------------- | ------------------------------------------------ |
| iOS / macOS    | SwiftUI (multiplatform) | Single codebase, native on both platforms        |
| CLI            | Python                  | Fast iteration, rich LLM/RAG library ecosystem   |
| Vector Search  | On-device (disk-backed) | No server dependency; disk index for large books |
| App Storage    | SwiftData               | Modern, native, works on both iOS and macOS      |
| CLI Storage    | SQLite + JSON files     | Simple, inspectable, mirrors app data model      |
| LLM (default)  | Anthropic (Claude)      | High quality, strong reasoning                   |
| LLM (alt)      | OpenAI / Local LLM      | User choice; local = fully offline               |
| Embeddings     | Provider-matched        | Use same provider's embedding model              |
| LLM Abstraction| Protocol/interface      | Swap providers without changing pipeline logic   |

### Data Flow

1. **Ingest**: Book file → parsed on-device → chunked (500-1000 tokens) → embedded via LLM API → vectors stored locally
2. **Query**: User question → embedded via LLM API → local vector similarity search → top-k chunks → sent with question to LLM API → streamed response

### LLM Provider Architecture

The app uses a provider abstraction (Swift protocol / Python base class) so the RAG pipeline is provider-agnostic. Each provider implements:
- `embed(text) → vector` — generate embeddings
- `complete(prompt, context) → stream` — generate a streamed answer

#### Supported Providers

| Provider   | Chat Model         | Embedding Model              | Notes                              |
| ---------- | ------------------ | ---------------------------- | ---------------------------------- |
| Anthropic  | Claude Sonnet/Opus | Voyage AI (or OpenAI embed)  | Default. API key required.         |
| OpenAI     | GPT-4o             | text-embedding-3-small       | API key required.                  |
| Local LLM  | User's choice      | User's choice                | Ollama / llama.cpp. Fully offline. |

**Note**: Anthropic doesn't have a native embedding API, so embeddings use a compatible provider (Voyage AI or OpenAI's embedding endpoint). This is handled transparently — the user just picks "Anthropic" and it works.

On iOS/macOS, API keys are stored in the Keychain. Local LLM endpoint URL is stored in UserDefaults.

## Non-Goals (v1)

- No backend server or database
- No web interface
- No user accounts or authentication
- No Android app
- No support for audiobooks or scanned image PDFs (OCR)
- No in-app book reader (this is a Q&A tool, not a reading app)

## Success Criteria

- User can upload a PDF or TXT book and ask questions within 2 minutes
- Answers are grounded in actual book content (not hallucinated)
- Source passages are shown alongside answers for verification
- Works fully offline after initial book ingestion (except LLM API calls; local LLM = fully offline)
- CLI can prototype and validate pipeline changes in seconds
- macOS and iOS share the same codebase with platform-appropriate UI

## Open Questions

- [ ] Large book vector index: FAISS on-disk, SQLite with vector extension, or custom solution?
- [ ] Use Apple's on-device NaturalLanguage framework for embeddings as a fourth "free" option?
- [ ] SwiftData vs Core Data? SwiftData is newer but Core Data is more battle-tested.
- [ ] How much RAG logic should be shared between app (Swift) and CLI (Python), or are they independent implementations?
- [ ] Anthropic embedding story: use Voyage AI, OpenAI embeddings, or something else?
- [ ] Local LLM: support Ollama only, or also llama.cpp / LM Studio?
