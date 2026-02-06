# Product Requirement Document: Interactive Books

## Overview

A local-only iOS app that lets users upload books and have conversations about them. All processing happens on-device or via direct API calls to an LLM provider — no backend server required. Users can ask questions, get summaries, find specific passages, and explore themes using RAG (retrieval-augmented generation).

A companion CLI tool is provided for debugging and development.

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
- **CLI** — Python command-line tool for debugging and testing the RAG pipeline

No backend server. No web interface.

## Core Features

### P0 — Must Have

1. **Book Upload**
   - Users can upload book files (PDF, TXT)
   - App parses, chunks, and indexes content locally
   - Upload from iOS Files picker

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
    - Sync book metadata and chat history via iCloud
    - Book content stays on-device (too large for sync)

## CLI Tool (Debug / Development)

A Python CLI that exercises the same RAG pipeline logic as the iOS app. Used for:

- **Testing ingestion**: `cli ingest <file>` — parse, chunk, embed a book and inspect the results
- **Testing retrieval**: `cli search <book> <query>` — run vector search and see retrieved chunks
- **Testing Q&A**: `cli ask <book> <question>` — full end-to-end question answering
- **Inspecting data**: `cli books` — list ingested books, chunk counts, metadata
- **Verbose output**: `--verbose` flag to log chunk boundaries, similarity scores, prompt construction, token counts

The CLI is not a user-facing product. It's a developer tool for validating and debugging the core pipeline before integrating into the iOS app.

## Technical Approach

### Architecture

```
┌──────────────────────────────┐
│         iOS App              │
│        (SwiftUI)             │
│                              │
│  ┌───────────┐ ┌──────────┐ │
│  │Book Ingest│ │Q&A Engine│ │
│  │ ├─ Parser │ │├─Retrieve│ │
│  │ ├─ Chunker│ ││ (local) │ │
│  │ └─ Embed  │ │└─LLM call│ │
│  └───────────┘ └──────────┘ │
│                              │
│  ┌──────────────────────┐   │
│  │    Local Storage      │   │
│  │  Core Data / SQLite   │   │
│  └──────────────────────┘   │
└──────────────┬───────────────┘
               │
               │ HTTPS
               ▼
       ┌───────────────┐
       │   LLM API     │
       │ (OpenAI /     │        ┌──────────────┐
       │  Anthropic)   │◄───────│  CLI (Python) │
       └───────────────┘        │  Debug tool   │
                                └──────────────┘
```

### Key Technical Decisions

| Decision       | Choice              | Rationale                                       |
| -------------- | ------------------- | ----------------------------------------------- |
| iOS            | SwiftUI             | Modern, declarative, native performance         |
| CLI            | Python              | Fast to build, same ecosystem as LLM libraries  |
| Vector Search  | In-memory / on-device| No server dependency, fast for small datasets  |
| iOS Storage    | Core Data / SQLite  | Native, reliable, handles structured + blob data|
| CLI Storage    | SQLite + JSON files | Simple, inspectable, mirrors iOS data model     |
| Embeddings     | LLM API (OpenAI)   | Only outbound API call needed                   |
| LLM            | TBD                 | OpenAI or Anthropic, user provides API key      |

### Data Flow

1. **Ingest**: Book file → parsed on-device → chunked (500-1000 tokens) → embedded via LLM API → vectors stored locally
2. **Query**: User question → embedded via LLM API → local vector similarity search → top-k chunks → sent with question to LLM API → streamed response

### Embedding Strategy

Embeddings are generated by calling the LLM provider's embedding API directly from the client. On iOS, the API key is stored in the Keychain.

## Non-Goals (v1)

- No backend server or database
- No web interface
- No user accounts or authentication
- No Android app
- No support for audiobooks or scanned image PDFs (OCR)
- No cross-device sync (each device is independent)
- No in-app book reader (this is a Q&A tool, not a reading app)

## Success Criteria

- User can upload a PDF or TXT book and ask questions within 2 minutes
- Answers are grounded in actual book content (not hallucinated)
- Source passages are shown alongside answers for verification
- Works fully offline after initial book ingestion (except LLM API calls)
- CLI can ingest a book and answer questions end-to-end for debugging

## Open Questions

- [ ] Which LLM provider to use? (OpenAI vs Anthropic)
- [ ] Should we support very large books (1000+ pages)? In-memory vector search may need optimization.
- [ ] iOS: use Apple's on-device NaturalLanguage framework for embeddings to avoid API calls during ingestion?
- [ ] How much RAG logic should be shared between iOS (Swift) and CLI (Python), or are they independent implementations?
