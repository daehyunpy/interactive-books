# Product Requirement Document: Interactive Books

## Overview

A mobile and web app that lets users upload books and have conversations about them. Users can ask questions, get summaries, find specific passages, and explore themes — all powered by an LLM with retrieval-augmented generation (RAG).

## Problem

Reading a book and retaining or finding specific information is time-consuming. Readers often want to:
- Quickly recall details from a book they've read
- Get summaries of chapters or sections
- Ask analytical questions ("What motivates character X?")
- Find specific passages without manually searching

## Target User

Individual readers who want a faster way to interact with and extract value from books they own.

## Platforms

- **iOS** — native app (Swift/SwiftUI)
- **Web** — responsive web app (React/Next.js)
- **Backend API** — shared backend serving both clients

## Core Features

### P0 — Must Have

1. **Book Upload**
   - Users can upload book files (PDF, TXT)
   - System ingests and indexes the content for search
   - Upload from device (iOS Files, camera roll) or drag-and-drop (web)

2. **Ask Questions**
   - Chat-style interface for asking questions about a book
   - System retrieves relevant passages and generates an answer
   - Answers include references to the source passages
   - Streaming responses for real-time feel

3. **Book Library**
   - Grid/list view of uploaded books with cover thumbnails
   - Users can select which book to chat about
   - Search and filter books

### P1 — Should Have

4. **Chapter Summaries**
   - Users can request a summary of a specific chapter or section
   - System identifies chapter boundaries and summarizes content

5. **Multi-Book Queries**
   - Users can ask questions across multiple books at once
   - Useful for comparing themes, characters, or ideas across works

6. **Chat History**
   - Conversation history is persisted per book
   - Users can revisit prior Q&A sessions

7. **User Accounts**
   - Sign up / sign in (email + social auth)
   - Books and chat history synced across devices

### P2 — Nice to Have

8. **EPUB Support**
   - Support for EPUB format in addition to PDF and TXT

9. **Highlights & Notes**
   - Users can save interesting passages or answers
   - Export notes as markdown

10. **Push Notifications (iOS)**
    - Notify when a large book finishes processing

11. **Offline Mode (iOS)**
    - Cache recent chats and book metadata for offline reading

## Technical Approach

### Architecture

```
┌──────────────┐    ┌──────────────┐
│   iOS App    │    │   Web App    │
│  (SwiftUI)   │    │  (Next.js)   │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └───────┬───────────┘
               │ REST / WebSocket
               ▼
       ┌───────────────┐
       │  Backend API   │
       │  (Python/Fast  │
       │    API)        │
       ├───────────────┤
       │ Ingestion Svc  │  Book file → parse → chunk → embed → store
       │ Retrieval Svc  │  Question → embed → vector search → top-k
       │ Q&A Service    │  Context + question → LLM → answer
       └───────┬───────┘
               │
       ┌───────┴────────┐
       │  Storage Layer  │
       ├────────────────┤
       │ Vector DB       │  (Pinecone / pgvector)
       │ App Database    │  (PostgreSQL)
       │ File Storage    │  (S3 / CloudKit)
       └────────────────┘
```

### Key Technical Decisions

| Decision          | Choice        | Rationale                                    |
| ----------------- | ------------- | -------------------------------------------- |
| iOS               | SwiftUI       | Modern, declarative, native performance      |
| Web Frontend      | Next.js       | SSR, great DX, easy deployment               |
| Backend           | FastAPI       | Async Python, great for LLM/RAG workloads    |
| Vector Store      | Pinecone      | Managed, scales without ops burden            |
| App Database      | PostgreSQL    | Reliable, supports pgvector as alternative    |
| File Storage      | S3            | Cheap, reliable, pre-signed upload URLs       |
| Embeddings        | OpenAI        | High quality, easy to set up                  |
| LLM              | TBD           | OpenAI or Anthropic                           |
| Auth              | Supabase Auth | Works well with both iOS and web              |

### Data Flow

1. **Ingest**: Book file → uploaded to S3 → backend parses text → chunked (500-1000 tokens) → embedded → stored in vector DB
2. **Query**: User question → embedded → top-k similar chunks retrieved → LLM generates answer with chunks as context → streamed to client

## Non-Goals (v1)

- No Android app (iOS and web only)
- No support for audiobooks or scanned image PDFs (OCR)
- No real-time collaboration or shared libraries
- No in-app book reader (this is a Q&A tool, not a reading app)

## Success Criteria

- User can upload a PDF or TXT book and ask questions within 2 minutes
- Answers are grounded in actual book content (not hallucinated)
- Source passages are shown alongside answers for verification
- iOS app feels native and responsive (no web views)
- Web and iOS share the same backend with feature parity

## Open Questions

- [ ] Which LLM provider to use? (OpenAI vs Anthropic)
- [ ] Should we support very large books (1000+ pages)? Chunking strategy may need tuning.
- [ ] Pinecone vs pgvector? Pinecone is simpler but adds a vendor dependency.
- [ ] Supabase vs Firebase for auth? Supabase is more open, Firebase has better iOS SDK.
- [ ] App Store review — any concerns with user-uploaded content?
