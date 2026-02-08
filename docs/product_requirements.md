# Product Requirements: Interactive Books

## Overview

A local-only iOS and macOS app that lets users upload books and have conversations about them. All processing happens on-device or via direct API calls to an LLM provider — no backend server required. Users can ask questions, get summaries, find specific passages, and explore themes using RAG (retrieval-augmented generation).

A Python CLI tool is provided for debugging and rapid prototyping.

## Problem

Reading a book and retaining or finding specific information is time-consuming. Readers often want to:
- Quickly recall details from a book they've read
- Get summaries of chapters or sections
- Ask analytical questions ("What motivates character X?")
- Find specific passages without manually searching

## Target User

Individual readers who want a faster way to interact with and extract value from books they own.

## Platforms

- **iOS** — native app, all data stored on-device
- **macOS** — native app, shared codebase with iOS
- **CLI** — command-line tool for debugging and quick prototyping

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
     - **Local LLM** — connect to a locally running model (e.g. Ollama)
   - Provider can be switched at any time; existing books and chat history are preserved

### P1 — Should Have

6. **Large Book Support (1000+ pages)**
   - Efficient chunking and indexing for very large books
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

A CLI for debugging and rapid prototyping. Used to iterate on the RAG pipeline quickly before implementing in the app.

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

## Non-Goals (v1)

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
