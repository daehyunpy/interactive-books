# Product Requirements: Interactive Books

## Overview

A local-only iOS and macOS app that lets users upload books and have ongoing conversations about them. All processing happens on-device or via direct API calls to an LLM provider — no backend server required. An agentic chat system maintains conversation context, decides when to retrieve relevant passages, and reformulates queries as the conversation evolves — grounding every answer in the actual text.

A Python CLI tool is provided for debugging and rapid prototyping.

## Vision

No existing reading platform — Apple Books, Kindle, Google Play Books, Kobo — lets readers use an LLM with the books they own. These platforms treat books as static files to display, not as knowledge to query. Interactive Books fills this gap.

The product starts as a local-only tool for LLM-powered reading. Once the interaction model is proven (ask questions, get spoiler-free answers with page citations, explore themes), it can grow into a broader interactive reading platform — publisher integrations, shared Q&A, curated collections, and eventually a marketplace where "interactive" is the default reading experience.

See [Product Brief](product_brief.md) for the full strategic context.

## Problem

Existing reading platforms don't offer LLM-powered interactions despite the technology being ready. Readers are left with passive tools while LLMs sit unused. At the individual level, this means:

- Quickly recalling details from a book requires flipping through pages or relying on memory
- Getting summaries of chapters or sections means re-reading or using generic AI that doesn't have the actual text
- Asking analytical questions ("What motivates character X?") has no good answer without the source material
- Finding specific passages without manually searching is tedious or impossible

Readers already use ChatGPT to discuss books — but without access to the actual text, answers are generic and unreliable. Interactive Books connects the LLM to the real content.

## Target User

Individual readers who want more from the books they already own. Early adopters comfortable with API keys and local apps. Students, researchers, and professionals who read deeply and need to recall, compare, and synthesize across books.

## Platforms

- **iOS** — native app, all data stored on-device
- **macOS** — native app, shared codebase with iOS
- **CLI** — command-line tool for debugging and quick prototyping

No backend server. No web interface.

## User Stories

### Student

- As a student reading a textbook, I want to ask questions about concepts from chapters I've already read so that I can deepen my understanding without spoiling later material.
- As a student preparing for an exam, I want to get summaries of specific chapters so that I can review efficiently.
- As a student, I want to ask questions across multiple textbooks so that I can connect ideas from different courses.
- As a student, I want to ask follow-up questions without repeating context so that my study session flows naturally like a conversation with a tutor.

### Researcher / Professional

- As a researcher, I want to upload a paper or book and ask about specific arguments so that I can quickly locate evidence without re-reading.
- As a professional, I want to search across multiple reference books at once so that I can compare approaches to a problem.
- As a researcher, I want page citations in every answer so that I can verify claims against the source material.
- As a researcher, I want the system to understand "compare that with chapter 5's argument" without me restating what "that" refers to, so I can work efficiently.

### General Reader

- As a reader midway through a novel, I want to ask "Who is this character?" without getting spoilers from later chapters.
- As a reader who finished a book weeks ago, I want to recall specific details so that I can discuss the book with others.
- As a privacy-conscious reader, I want to use a local LLM so that my reading data never leaves my device.
- As a reader, I want to continue a conversation about a book where I left off yesterday so that I don't lose my train of thought.

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

3. **Book Conversations**
   - Chat-style interface for multi-turn conversations about a book
   - The agent maintains conversation history within a session and uses it to interpret follow-up questions (e.g., "Tell me more about that character" resolves to the character discussed in the previous turn)
   - The agent decides when to retrieve passages from the book — not every message requires retrieval (e.g., clarifying questions, follow-ups on already-retrieved context, or meta-questions about the conversation)
   - When retrieval is needed, the agent reformulates the user's message into a self-contained search query using conversation context before searching
   - Answers include page number references to source passages
   - Users can reference pages in questions (e.g. "What did the author mean on p.73?", "Summarize pages 100-120")
   - Page references in answers are tappable — jump to that page's context
   - Streaming responses for real-time feel

   **Edge cases:**
   - PDF with unreliable page numbers (e.g., front matter numbered separately): use physical page index as fallback, note discrepancy to user
   - Pages that fail to parse (scanned pages in an otherwise text PDF): skip and mark as unparseable; inform user which pages are missing
   - User asks about a page beyond what was successfully parsed: tell the user that page couldn't be processed and suggest nearby pages
   - TXT files with no page structure: divide into estimated pages by character count; label as "estimated page" in citations

4. **Book Library**
   - Grid/list view of uploaded books
   - Users can select which book to chat about
   - Search and filter books

5. **LLM Provider Selection**
   - User chooses their LLM provider in settings:
     - **Anthropic (Claude)** — default provider
     - **OpenAI (GPT)**
     - **Local LLM** — connect to a locally running model (e.g. Ollama)
   - Provider can be switched at any time; existing books and conversations are preserved

6. **Conversation Sessions**
   - Each book can have multiple conversations (e.g., one for study notes, one for casual reading)
   - A conversation preserves the full message history (user and assistant turns)
   - The agent uses conversation history as context when interpreting new messages
   - Conversations are titled automatically from the first message; users can rename them
   - Conversations are persisted locally and survive app restarts
   - Users can start a new conversation or continue an existing one
   - Deleting a book deletes all its conversations (cascade)

### P1 — Should Have

7. **Large Book Support (1000+ pages)**
   - Efficient chunking and indexing for very large books
   - Background ingestion with progress indicator
   - Incremental embedding (resume if interrupted)

8. **Chapter Summaries**
   - Users can request a summary of a specific chapter or section
   - App identifies chapter boundaries and summarizes content

9. **Multi-Book Queries**
   - Users can ask questions across multiple books at once
   - Useful for comparing themes, characters, or ideas across works

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
- `cli chat <book>` — interactive conversation mode with session persistence
- `cli books` — list ingested books, chunk counts, metadata
- `--verbose` flag — log chunk boundaries, similarity scores, prompt construction, token counts

### Role

The CLI serves two purposes:

1. **Prototyping** — quickly test different chunking strategies, embedding models, prompt templates, and retrieval parameters without rebuilding an Xcode project
2. **Debugging** — inspect intermediate pipeline state (chunks, embeddings, retrieved context, final prompt) when something isn't working

The CLI is not a user-facing product.

## Privacy & Data Handling

Local-first is a core value proposition, not just an architecture choice. Users must understand exactly what stays on their device and what doesn't.

| Data                   | Where it lives                | Leaves the device?                                         |
| ---------------------- | ----------------------------- | ---------------------------------------------------------- |
| Book files (PDF, TXT)  | Local storage only            | Never                                                      |
| Parsed text and chunks | Local SQLite DB               | Only when sent to LLM API as context for a question        |
| Embeddings             | Local SQLite DB (sqlite-vec)  | Never (computed via API, stored locally)                   |
| Conversation history   | Local SQLite DB               | Message content is sent to LLM API as conversation context |
| API keys               | Keychain (app) / `.env` (CLI) | Sent to LLM provider for authentication                    |
| Reading position       | Local SQLite DB               | Never                                                      |

**What gets sent to external APIs:**

- When using a cloud LLM (Anthropic, OpenAI): the user's question and retrieved text chunks are sent to the provider's API. This is the minimum needed to generate an answer.
- When using a cloud embedding provider: chunk text is sent to generate embeddings. This happens once at ingestion time.
- When using Ollama (local LLM + local embeddings): nothing leaves the device. Fully offline.

**No telemetry, no analytics, no accounts.** v1 collects nothing. If usage analytics are added later (see Success Criteria), they will be opt-in and local-only.

## Non-Goals (v1)

- **No Android app** — iOS/macOS first to validate the concept
- **No audiobooks or scanned image PDFs (OCR)** — text-based formats only; OCR adds complexity without validating the core interaction
- **No in-app book reader** — this is a Q&A tool, not a reading app; users read in their preferred app and come here to interact
- **No social features** — no shared libraries, collaborative annotations, or public Q&A; local-only in v1
- **No book purchasing or DRM support** — users bring their own DRM-free files; no store, no rights management
- **No web app** — native only; web adds deployment complexity without validating the mobile/desktop experience
- **No user accounts or cloud backend** — no sign-up, no server, no data collection
- **No custom model fine-tuning** — use off-the-shelf LLMs via standard APIs; fine-tuning is a future optimization

## Success Criteria

### Leading Indicators (validate during development)

| Metric               | Target                                                            | How to measure                                                   |
| -------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| Ingestion time       | < 2 min for a 300-page PDF                                        | Time from upload to "ready" status                               |
| Retrieval accuracy   | Top-5 chunks contain the relevant passage ≥ 80% of the time       | Manual evaluation on a test set of 20 questions per sample book  |
| Citation rate        | ≥ 90% of answers include at least one page citation               | Automated check on LLM output                                    |
| Answer groundedness  | < 10% of answers contain claims not traceable to retrieved chunks | Manual spot-check against source passages                        |
| Ingestion throughput | ≥ 50 pages/sec for chunking + embedding                           | Benchmark on sample books                                        |
| Anaphora resolution  | Agent correctly resolves references ≥ 80% of the time             | Manual evaluation on 10 multi-turn conversations per sample book |

### Lagging Indicators (validate post-launch)

| Metric                 | Target                                              | How to measure                                   |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------ |
| Time to first question | < 5 min from app install to first answered question | Analytics event (if added later) or user testing |
| Return usage           | User asks ≥ 3 questions per book on average         | Local usage stats (opt-in)                       |
| Multi-book adoption    | ≥ 30% of users upload 2+ books within first month   | Local usage stats (opt-in)                       |

### Functional Requirements

- Source passages are shown alongside answers for verification
- Works fully offline after initial book ingestion (except LLM API calls; local LLM = fully offline)
- CLI can prototype and validate pipeline changes in seconds
- macOS and iOS share the same codebase with platform-appropriate UI
