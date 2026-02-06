# Product Requirement Document: Interactive Books

## Overview

A tool that lets users upload books and have conversations about them. Users can ask questions, get summaries, find specific passages, and explore themes — all powered by an LLM with retrieval-augmented generation (RAG).

## Problem

Reading a book and retaining or finding specific information is time-consuming. Readers often want to:
- Quickly recall details from a book they've read
- Get summaries of chapters or sections
- Ask analytical questions ("What motivates character X?")
- Find specific passages without manually searching

## Target User

Individual readers who want a faster way to interact with and extract value from books they own.

## Core Features

### P0 — Must Have

1. **Book Upload**
   - Users can upload book files (PDF, TXT)
   - System ingests and indexes the content for search

2. **Ask Questions**
   - Users type a question about an uploaded book
   - System retrieves relevant passages and generates an answer
   - Answers include references to the source passages

3. **Book Library**
   - Users can see a list of their uploaded books
   - Users can select which book to chat about

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

### P2 — Nice to Have

7. **EPUB Support**
   - Support for EPUB format in addition to PDF and TXT

8. **Highlights & Notes**
   - Users can save interesting passages or answers
   - Export notes as markdown

9. **Web UI**
   - Streamlit or similar lightweight web interface
   - Book selection sidebar, chat window, source panel

## Technical Approach

### Architecture

```
User Interface (CLI / Web)
        │
        ▼
   Application Layer
   ├── Book Ingestion Service
   │   ├── File parser (PDF, TXT)
   │   ├── Text chunker
   │   └── Embedding generator
   ├── Retrieval Service
   │   └── Vector similarity search
   └── Q&A Service
       └── LLM prompt with retrieved context
        │
        ▼
   Storage Layer
   ├── Vector DB (ChromaDB / FAISS)
   └── Book metadata (SQLite / JSON)
```

### Key Technical Decisions

| Decision          | Choice      | Rationale                          |
| ----------------- | ----------- | ---------------------------------- |
| Language          | Python      | Best ecosystem for LLM/RAG tooling |
| LLM Framework    | LangChain   | Mature, well-documented            |
| Vector Store     | ChromaDB    | Simple, no server needed           |
| Embeddings       | OpenAI      | High quality, easy to set up       |
| LLM              | TBD         | OpenAI or Anthropic                |
| Interface (v1)   | CLI         | Fastest to build                   |
| Interface (v2)   | Streamlit   | Low-effort web UI                  |

### Data Flow

1. **Ingest**: Book file → parsed text → chunked (500-1000 tokens) → embedded → stored in vector DB
2. **Query**: User question → embedded → top-k similar chunks retrieved → LLM generates answer with chunks as context

## Non-Goals (v1)

- No user authentication or multi-tenancy
- No hosted/cloud deployment
- No support for audiobooks or scanned image PDFs (OCR)
- No real-time collaboration

## Success Criteria

- User can upload a PDF or TXT book and ask questions within 2 minutes
- Answers are grounded in actual book content (not hallucinated)
- Source passages are shown alongside answers for verification

## Open Questions

- [ ] Which LLM provider to use? (OpenAI vs Anthropic)
- [ ] Should we support very large books (1000+ pages)? Chunking strategy may need tuning.
- [ ] Local-only or allow cloud vector storage later?
