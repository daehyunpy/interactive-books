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

2. **Reading Position & Page-Aware Q&A**
   - User sets their current page/position in the book
   - App uses this as context when answering — answers are scoped to what the user has read so far
   - Avoids spoilers: LLM is instructed not to reveal content beyond the user's current page
   - Answers cite specific page numbers (e.g. "As mentioned on p.42...")
   - Position is saved per book and persists across sessions

3. **Ask Questions**
   - Chat-style interface for asking questions about a book
   - App retrieves relevant passages locally, sends them with the question to an LLM API
   - Answers include page number references to source passages
   - Users can reference pages in questions (e.g. "What did the author mean on p.73?", "Summarize pages 100-120")
   - Page references in answers are tappable — jump to that page's context
   - Streaming responses for real-time feel

4. **Book Library**
   - Grid/list view of uploaded books
   - Users can select which book to chat about
   - Search and filter books

5. **LLM Provider Selection**
   - User chooses their LLM provider in settings:
     - **Anthropic (Claude)** — default provider
     - **OpenAI (GPT)**
     - **Local LLM** — connect to a locally running model (e.g. Ollama, llama.cpp server)
   - API key stored in Keychain (Anthropic / OpenAI)
   - Local LLM: user configures endpoint URL (e.g. `http://localhost:11434`)
   - Provider can be switched at any time; existing books and chat history are preserved

### P1 — Should Have

6. **Large Book Support (1000+ pages)**
   - Efficient chunking and indexing for very large books
   - On-disk vector index (not purely in-memory) to handle large embedding sets
   - Background ingestion with progress indicator
   - Incremental embedding (resume if interrupted)

7. **Chapter Summaries**
   - Users can request a summary of a specific chapter or section
   - App identifies chapter boundaries and summarizes content

8. **Multi-Book Queries**
   - Users can ask questions across multiple books at once
   - Useful for comparing themes, characters, or ideas across works

9. **Chat History**
   - Conversation history is persisted locally per book
   - Users can revisit prior Q&A sessions

### P2 — Nice to Have

10. **EPUB Support**
    - Support for EPUB format in addition to PDF and TXT

11. **Highlights & Notes**
    - Users can save interesting passages or answers
    - Export notes as markdown

12. **iCloud Sync**
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

### Key Technical Decisions

| Decision       | Choice                  | Rationale                                        |
| -------------- | ----------------------- | ------------------------------------------------ |
| iOS / macOS    | SwiftUI (multiplatform) | Single codebase, native on both platforms        |
| CLI            | Python                  | Fast iteration, rich LLM/RAG library ecosystem   |
| Vector Search  | SQLite + sqlite-vec     | Native on Apple, single DB, handles large books  |
| App Storage    | SwiftData               | Modern stack, native, works on both iOS and macOS|
| CLI Storage    | SQLite + JSON files     | Simple, inspectable, mirrors app data model      |
| LLM (default)  | Anthropic (Claude)      | High quality, strong reasoning                   |
| LLM (alt)      | OpenAI / Local LLM      | User choice; local = fully offline               |
| Embeddings     | Provider-matched        | Use same provider's embedding model              |
| LLM Abstraction| Protocol/interface      | Swap providers without changing pipeline logic   |

### Data Flow

1. **Ingest**: Book file → parsed on-device → page boundaries mapped → chunked (500-1000 tokens, preserving page numbers) → embedded via LLM API → vectors + page metadata stored locally
2. **Query**: User question + current page position → embedded via LLM API → local vector similarity search (filtered to pages ≤ current position by default) → top-k chunks with page numbers → sent with question to LLM API → streamed response with page citations

### Page Mapping

Each chunk stores its source page number(s). This enables:
- **Page-scoped retrieval**: only search content up to the user's current page (no spoilers)
- **Page references in answers**: LLM cites specific pages in responses
- **Page-based queries**: user can ask about specific pages or page ranges
- **Tappable citations**: page references in answers link back to the chunk's source content

For PDFs, page numbers come directly from the document structure. For TXT files, pages are estimated by character/line count or user-defined page breaks.

### LLM Provider Architecture

The app uses a provider abstraction (Swift protocol / Python base class) so the RAG pipeline is provider-agnostic. Each provider implements:
- `embed(text) → vector` — generate embeddings
- `complete(prompt, context) → stream` — generate a streamed answer

#### Supported Providers

| Provider        | Chat Model         | Embedding Model              | Notes                              |
| --------------- | ------------------ | ---------------------------- | ---------------------------------- |
| Anthropic       | Claude Sonnet/Opus | Voyage AI (or OpenAI embed)  | Default. API key required.         |
| OpenAI          | GPT-4o             | text-embedding-3-small       | API key required.                  |
| Local LLM       | User's choice      | User's choice                | Ollama (v1). Fully offline.        |
| Apple (on-device)| —                 | NaturalLanguage framework    | Free, offline embeddings only.     |

**Notes**:
- Anthropic doesn't have a native embedding API, so embeddings use a compatible provider (Voyage AI or OpenAI's embedding endpoint). This is handled transparently — the user just picks "Anthropic" and it works.
- Apple's on-device NaturalLanguage framework provides free, offline embeddings. Can be used with any chat provider to avoid embedding API costs, or paired with Ollama for a fully offline, zero-cost setup.

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

- [x] ~~Large book vector index: FAISS on-disk, SQLite with vector extension, or custom solution?~~ **SQLite + sqlite-vec** — native on Apple platforms, everything in one DB.
- [x] ~~Use Apple's on-device NaturalLanguage framework for embeddings as a fourth "free" option?~~ **Yes** — add as a free, offline embedding option alongside API-based providers.
- [x] ~~SwiftData vs Core Data?~~ **SwiftData** — prefer modern stack.
- [ ] How much RAG logic should be shared between app (Swift) and CLI (Python), or are they independent implementations?
- [ ] Anthropic embedding story: use Voyage AI, OpenAI embeddings, or something else?
- [x] ~~Local LLM: support Ollama only, or also llama.cpp / LM Studio?~~ **Ollama first** (most popular). Others based on market response.
