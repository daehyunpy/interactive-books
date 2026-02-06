# Product Requirement Document: Interactive Books

## Overview

A local-only iOS and web app that lets users upload books and have conversations about them. All processing happens on-device or via direct API calls to an LLM provider — no backend server required. Users can ask questions, get summaries, find specific passages, and explore themes using RAG (retrieval-augmented generation).

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
- **Web** — client-side web app (React/Next.js static export), all data stored in browser

No backend server. Each platform is fully self-contained.

## Core Features

### P0 — Must Have

1. **Book Upload**
   - Users can upload book files (PDF, TXT)
   - App parses, chunks, and indexes content locally
   - Upload from device (iOS Files) or drag-and-drop (web)

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
   - User provides their own LLM API key (stored locally)
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

10. **iCloud Sync (iOS)**
    - Sync book metadata and chat history via iCloud
    - Book content stays on-device (too large for sync)

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────┐
│              Client App                  │
│  (iOS: SwiftUI  /  Web: Next.js static) │
│                                          │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ Book Ingest  │  │  Q&A Engine      │  │
│  │ ├─ Parser    │  │  ├─ Retrieval    │  │
│  │ ├─ Chunker   │  │  │  (local vec   │  │
│  │ └─ Embedder  │  │  │   search)     │  │
│  │   (LLM API)  │  │  └─ LLM call    │  │
│  └─────────────┘  │     (API)         │  │
│                    └──────────────────┘  │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │         Local Storage             │   │
│  │  iOS: Core Data / SQLite + files  │   │
│  │  Web: IndexedDB + localStorage    │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
               │
               │ HTTPS (only outbound call)
               ▼
       ┌───────────────┐
       │   LLM API     │
       │ (OpenAI /     │
       │  Anthropic)   │
       └───────────────┘
```

### Key Technical Decisions

| Decision          | Choice                 | Rationale                                       |
| ----------------- | ---------------------- | ----------------------------------------------- |
| iOS               | SwiftUI                | Modern, declarative, native performance         |
| Web               | Next.js (static)       | Static export, no server needed, good DX        |
| Vector Search     | In-memory / on-device  | No server dependency, fast for small datasets   |
| iOS Storage       | Core Data / SQLite     | Native, reliable, handles structured + blob data|
| Web Storage       | IndexedDB              | Large storage capacity in browser               |
| Embeddings        | LLM API (OpenAI)       | Only outbound API call needed                   |
| LLM              | TBD                    | OpenAI or Anthropic, user provides API key      |
| Deployment (web)  | Static hosting         | GitHub Pages, Vercel static, or Netlify         |

### Data Flow

1. **Ingest**: Book file → parsed on-device → chunked (500-1000 tokens) → embedded via LLM API → vectors stored locally
2. **Query**: User question → embedded via LLM API → local vector similarity search → top-k chunks → sent with question to LLM API → streamed response

### Embedding Strategy (No Server)

Since there's no backend, embeddings are generated by calling the LLM provider's embedding API directly from the client. For the web app, this means the API key is used client-side — acceptable for a personal tool but noted as a trade-off.

For iOS, the API key is stored in the Keychain. For web, it's stored in localStorage (user's own browser, user's own key).

## Non-Goals (v1)

- No backend server or database
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
- No server to deploy or maintain

## Open Questions

- [ ] Which LLM provider to use? (OpenAI vs Anthropic)
- [ ] Should we support very large books (1000+ pages)? In-memory vector search may need optimization.
- [ ] Web: is client-side embedding API call acceptable, or should we limit to iOS only at first?
- [ ] iOS: use Apple's on-device NaturalLanguage framework for embeddings to avoid API calls during ingestion?
