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

4. **API Key Configuration**
   - User provides their own LLM API key (stored in Keychain)
   - Settings screen to enter/update key

### P1 — Should Have

5. **Chapter Summaries**
   - Users can request a summary of a specific chapter or section
   - App identifies chapter boundaries and summarizes content

6. **Multi-Book Queries**
   - Users can ask questions across multiple books at once
   - Useful for comparing themes, characters, or ideas across works

7. **Chat History**
   - Conversation history is persisted locally per book
   - Users can revisit prior Q&A sessions

### P2 — Nice to Have

8. **EPUB Support**
   - Support for EPUB format in addition to PDF and TXT

9. **Highlights & Notes**
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
| Vector Search  | In-memory / on-device   | No server dependency, fast for small datasets    |
| App Storage    | SwiftData               | Modern, native, works on both iOS and macOS      |
| CLI Storage    | SQLite + JSON files     | Simple, inspectable, mirrors app data model      |
| Embeddings     | LLM API (OpenAI)        | Only outbound API call needed                    |
| LLM            | TBD                     | OpenAI or Anthropic, user provides API key       |

### Data Flow

1. **Ingest**: Book file → parsed on-device → chunked (500-1000 tokens) → embedded via LLM API → vectors stored locally
2. **Query**: User question → embedded via LLM API → local vector similarity search → top-k chunks → sent with question to LLM API → streamed response

### Embedding Strategy

Embeddings are generated by calling the LLM provider's embedding API directly from the client. On iOS/macOS, the API key is stored in the Keychain.

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
- Works fully offline after initial book ingestion (except LLM API calls)
- CLI can prototype and validate pipeline changes in seconds
- macOS and iOS share the same codebase with platform-appropriate UI

## Open Questions

- [ ] Which LLM provider to use? (OpenAI vs Anthropic)
- [ ] Should we support very large books (1000+ pages)? In-memory vector search may need optimization.
- [ ] Use Apple's on-device NaturalLanguage framework for embeddings to avoid API calls during ingestion?
- [ ] SwiftData vs Core Data? SwiftData is newer but Core Data is more battle-tested.
- [ ] How much RAG logic should be shared between app (Swift) and CLI (Python), or are they independent implementations?
