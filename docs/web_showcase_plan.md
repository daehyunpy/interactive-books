# Web Showcase: Plan

## Purpose

Interactive Books is a portfolio project demonstrating full-stack engineering across three platforms — Python CLI, Swift native app, and a web interface. The web showcase exists to let hiring managers and recruiters **try the product instantly** without installing anything. It also demonstrates breadth: the same RAG pipeline implemented in Python, Swift, and TypeScript, sharing a common schema and prompt contract.

## Goals

1. **Instant demo** — a reviewer visits a URL and chats with a pre-loaded book within seconds. No setup, no API key, no install.
2. **Show full-stack range** — Python backend (FastAPI), TypeScript frontend (React), shared SQL schema, shared prompt templates. Three languages, one domain model.
3. **Prove system design thinking** — the web layer is a thin API over the same use cases that power the CLI and Swift app. Same domain, same contracts, different adapter.
4. **Keep it cheap** — free-tier hosting, ephemeral data, no persistent infrastructure. This is a demo, not a SaaS product.

## Non-Goals

- Production-grade deployment (auto-scaling, monitoring, multi-region)
- User accounts or authentication
- Persistent data across server restarts — every visitor gets a fresh session
- Book upload from the web UI (v1 uses a pre-seeded demo book only)
- Replacing or competing with the native iOS/macOS/visionOS app

## Demo Book

The demo ships with a pre-seeded book so reviewers see content immediately.

**Current dev book:** *1984* by George Orwell. Used during development for its recognizable content and rich themes.

> **Copyright note:** *1984* is under US copyright until 2045 (public domain in UK/EU/Canada/Australia). Before public deployment, switch to a public domain alternative. Do not ship a copyrighted text to a publicly hosted demo.

**Public domain candidates for production:**

| Book | Author | Why |
|------|--------|-----|
| *Pride and Prejudice* | Jane Austen | Universally known, rich dialogue, good for Q&A |
| *The Great Gatsby* | F. Scott Fitzgerald | US public domain since 2021, strong narrative themes |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Frontend (Vite + React)                  │
│              Hosted on Vercel                         │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │   Book Reader     │  │   Chat Panel              │ │
│  │   (page text,     │  │   (messages, input,       │ │
│  │    page nav,      │◄─┤    streaming, citations)  │ │
│  │    reading pos)   │  │                           │ │
│  └──────────────────┘  └──────────────────────────┘ │
│          ▲                        │                   │
│          └── page sync ───────────┘                   │
└────────────────────────┬─────────────────────────────┘
                         │ HTTPS (REST + SSE)
                         ▼
┌──────────────────────────────────────────────────────┐
│              Backend (FastAPI)                        │
│              Hosted on Render                         │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  Existing Python Use Cases                      │  │
│  │  (ChatWithBook, Search, ListBooks, etc.)        │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  SQLite + sqlite-vec (ephemeral, pre-seeded)    │  │
│  └────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────┘
                         │ HTTPS
                         ▼
                  ┌───────────────┐
                  │   LLM API     │
                  │  (Anthropic)  │
                  └───────────────┘
```

### Core UX: Split-Pane Reading + Chat

The main view is a **side-by-side layout**: book reader on the left, chat on the right. This mirrors how a reader actually uses the product — reading a book while asking questions about it.

**Page sync** ties the two panels together:

| Trigger | Effect |
|---------|--------|
| User navigates to a page in the reader | Updates reading position → chat retrieval is scoped to pages up to that point (spoiler-free) |
| Chat citation clicked (e.g., `(p.42)`) | Reader scrolls to page 42 and highlights the referenced passage |
| User sets reading position via slider/input | Both panels reflect the new position |

This is the product's key differentiator — **spoiler-free, page-aware chat** — and the web demo must show it clearly.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | Vite + React | Industry standard, pairs cleanly with a separate backend |
| Backend framework | FastAPI | Already a Python project; FastAPI is async, auto-generates OpenAPI docs |
| API style | REST + SSE for streaming | Simple, well-understood; SSE for token-by-token chat streaming |
| Database | Ephemeral SQLite + sqlite-vec | Same DB as CLI. Pre-seeded on startup. No persistent disk needed. |
| State model | Ephemeral per deploy | Conversations reset on server restart. Acceptable for a demo. |
| Hosting (frontend) | Vercel | Free tier, git-push deploy, static SPA |
| Hosting (backend) | Render | Free tier, supports Python, sufficient for demo traffic |
| API key management | Server-side only | Anthropic key stored as env var on Render. Never exposed to browser. |
| Demo book | Pre-seeded at startup | A sample book (from `shared/fixtures/`) pre-ingested and pre-embedded. Reviewers see content immediately. |

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React | 19+ |
| Build tool | Vite | 6+ |
| Data fetching | TanStack Query | 5+ |
| Styling | Tailwind CSS | 4+ |
| HTTP client | fetch (native) | — |
| Backend | FastAPI | 0.115+ |
| Streaming | Server-Sent Events (SSE) | — |
| Database | SQLite + sqlite-vec | Same as CLI |
| Linting (TS) | ESLint + Prettier | Latest |
| Testing (TS) | Vitest | Latest |
| Testing (Python) | pytest | Existing |

## API Design

The backend exposes a thin REST API over the existing Python use cases. No new domain logic — just HTTP adapters.

### Endpoints

| Method | Path | Use Case | Notes |
|--------|------|----------|-------|
| `GET` | `/api/books` | `ListBooksUseCase` | Returns all books (demo: just one) |
| `GET` | `/api/books/{id}` | `ListBooksUseCase` | Book detail with chunk count, status, total pages |
| `GET` | `/api/books/{id}/pages` | `ChunkRepository` | Page list with page numbers. Query: `?page=N` for single page text content |
| `PUT` | `/api/books/{id}/current-page` | `SetCurrentPageUseCase` | Update reading position. Body: `{ "page": N }` |
| `GET` | `/api/books/{id}/conversations` | `ManageConversationsUseCase` | List conversations for a book |
| `POST` | `/api/books/{id}/conversations` | `ManageConversationsUseCase` | Create a new conversation |
| `DELETE` | `/api/conversations/{id}` | `ManageConversationsUseCase` | Delete a conversation |
| `GET` | `/api/conversations/{id}/messages` | `ManageConversationsUseCase` | Get message history |
| `POST` | `/api/conversations/{id}/messages` | `ChatWithBookUseCase` | Send a message, get SSE response stream |
| `GET` | `/api/health` | — | Health check for Render |

### Streaming

`POST /api/conversations/{id}/messages` returns an SSE stream:

```
event: token
data: {"text": "The"}

event: token
data: {"text": " author"}

event: tool_use
data: {"name": "search_book", "query": "main theme"}

event: tool_result
data: {"results": [...]}

event: done
data: {"message_id": "abc123", "usage": {"input_tokens": 500, "output_tokens": 120}}
```

## Directory Structure

```
web/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── routes/
│   │   │   ├── books.py         # Book endpoints
│   │   │   ├── conversations.py # Conversation + message endpoints
│   │   │   └── health.py        # Health check
│   │   ├── deps.py              # Dependency injection (use cases)
│   │   └── seed.py              # Pre-seed demo book on startup
│   ├── pyproject.toml           # FastAPI + uvicorn deps
│   └── Dockerfile               # For Render deployment
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # Entry point
│   │   ├── App.tsx              # Router + layout
│   │   ├── api/                 # API client + TanStack Query hooks
│   │   │   ├── client.ts        # Base fetch wrapper
│   │   │   ├── books.ts         # useBooks, useBook, usePages hooks
│   │   │   └── chat.ts          # useConversations, useSendMessage hooks
│   │   ├── components/
│   │   │   ├── Layout.tsx       # Shell + navigation
│   │   │   ├── BookReader.tsx   # Page text display, page nav, reading position
│   │   │   ├── PageNav.tsx      # Prev/next, page slider, page number input
│   │   │   ├── SplitPane.tsx    # Side-by-side reader + chat with resizable divider
│   │   │   ├── ChatView.tsx     # Message list + input
│   │   │   └── MessageBubble.tsx # Single message with clickable citation links
│   │   ├── hooks/
│   │   │   ├── useSSE.ts        # SSE stream consumer
│   │   │   └── usePageSync.ts   # Shared reading position state + citation navigation
│   │   └── types/
│   │       └── api.ts           # Shared API types
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── README.md                    # Setup + deploy instructions
```

## Dev Plan

### Phase W-A: Backend API

Expose the existing Python use cases over HTTP.

#### Tasks

1. **FastAPI app scaffold** — `web/backend/` with FastAPI, uvicorn, CORS middleware. Health check endpoint.

2. **Dependency injection** — wire existing use cases (`ChatWithBookUseCase`, `ManageConversationsUseCase`, `ListBooksUseCase`) into FastAPI's dependency system.

3. **Book endpoints** — `GET /api/books`, `GET /api/books/{id}`. Read-only, returns JSON.

4. **Page content endpoint** — `GET /api/books/{id}/pages?page=N`. Returns the text content of a single page. Without `?page`, returns the page list (page numbers and metadata). This powers the book reader.

5. **Reading position endpoint** — `PUT /api/books/{id}/current-page`. Updates the reading position. The chat's retrieval scope is filtered to pages up to this position (spoiler-free).

6. **Conversation endpoints** — `GET`, `POST`, `DELETE` for conversations. `GET` for messages.

5. **Chat endpoint with SSE streaming** — `POST /api/conversations/{id}/messages`. Accepts `{ "content": "..." }`, returns SSE stream with tokens, tool events, and done event.

6. **Demo seed script** — on startup, check if demo book exists. If not, ingest + embed `shared/fixtures/sample_book.pdf` into an ephemeral SQLite DB.

7. **Tests** — API route tests with `httpx.AsyncClient` (FastAPI test client). Mock use cases for unit tests; integration test with real DB for the seed flow.

#### Acceptance Criteria

- `uvicorn api.main:app` starts and serves endpoints
- All endpoints return correct JSON
- SSE streaming delivers tokens incrementally
- Demo book is auto-seeded on cold start
- Existing Python tests still pass (no regressions)

---

### Phase W-B: Frontend Shell + Book Reader

Set up the React project, build the split-pane layout, and implement the book reader.

#### Tasks

1. **Vite + React scaffold** — `web/frontend/` with TypeScript, Tailwind CSS, ESLint, Prettier.

2. **API client** — typed fetch wrapper pointing at the backend URL. TanStack Query provider.

3. **Split-pane layout** — the main view is a resizable side-by-side layout: book reader (left) and chat panel (right). Desktop: both visible with draggable divider. Mobile: tabbed or swipeable (reader / chat).

4. **Book reader component** — fetches page text from `/api/books/{id}/pages?page=N` and displays it. Includes:
   - Page text area (scrollable, readable typography)
   - Page navigation: prev/next buttons, page number input, page slider
   - Current page indicator (e.g., "Page 42 of 328")

5. **Reading position sync** — `usePageSync` hook manages shared state:
   - When user navigates pages in the reader → calls `PUT /api/books/{id}/current-page` to update backend
   - Reading position is the source of truth for spoiler-free retrieval

6. **Book list / selection** — fetch from `/api/books`, display in a header or sidebar. Click to select (demo: single book, but the UI supports multiple).

7. **Routing** — React Router with routes: `/` (redirects to demo book), `/books/:id` (split-pane: reader + chat).

#### Acceptance Criteria

- `npm run dev` starts the app
- Book reader displays page text and supports navigation (prev/next/jump)
- Reading position persists via API call
- Split-pane layout works on desktop, stacked/tabbed on mobile
- Book list loads from the API

---

### Phase W-C: Chat Interface + Page Sync

The core feature — conversational chat with streaming, synced to the book reader.

#### Tasks

1. **Chat view** — message list with user/assistant bubbles. Auto-scroll to latest. Sits in the right pane of the split layout.

2. **Message input** — text field with send button. Disabled while streaming. Enter to send.

3. **SSE consumer hook** — `useSSE` hook that opens an SSE connection to `POST /api/conversations/{id}/messages` and progressively renders tokens.

4. **Streaming display** — assistant message appears and grows as tokens arrive. Typing indicator before first token.

5. **Clickable page citations** — parse `(p.42)` and `(pp.42-43)` patterns in assistant messages. Render as styled clickable badges. **On click: navigate the book reader to that page.** This is the key sync interaction — the reviewer sees the cited passage in context.

6. **Page sync integration** — wire citations to `usePageSync` hook from Phase W-B:
   - Citation click → reader navigates to the cited page
   - Reader page change → updates reading position for next chat query
   - Visual indicator in the reader when a cited passage is highlighted

7. **Tool use visibility** — optional toggle to show search queries and results (debug mode, like CLI `--verbose`).

8. **Conversation management** — create new, switch between, delete conversations. Conversation list in a collapsible panel or dropdown within the chat pane.

9. **Tests** — Vitest component tests for ChatView and MessageBubble. Integration test for SSE hook with a mock event source. Test citation click triggers page navigation.

#### Acceptance Criteria

- Multi-turn conversation works with streaming
- Tokens render progressively (not all at once)
- Clicking a page citation in chat navigates the book reader to that page
- Changing reading position in the reader scopes subsequent chat retrieval
- New conversations can be created and switched
- Chat history loads on conversation switch

---

### Phase W-D: Polish & Deploy

Make it demo-ready and deploy.

#### Tasks

1. **Loading states** — skeleton loaders for book list, chat history. Spinner during embedding check.

2. **Error handling** — friendly messages for API errors, network failures. "Server waking up" message for Render cold starts.

3. **Empty states** — "Start a conversation" prompt when no messages. "Select a book" when nothing selected.

4. **Mobile responsiveness** — test on phone-width viewports. Ensure chat input stays fixed at bottom.

5. **Dark mode** — Tailwind dark mode support. Match system preference.

6. **Deploy backend to Render** — Dockerfile, environment variables (`ANTHROPIC_API_KEY`), health check config.

7. **Deploy frontend to Vercel** — connect repo, set `web/frontend/` as root directory, configure API URL env var.

8. **README** — setup instructions for local dev and deployment.

#### Acceptance Criteria

- Live URL works end-to-end (visit → see demo book → chat → get answers with citations)
- Render cold start shows a friendly loading message, not a broken page
- Mobile layout is usable
- Dark mode works
- Both deploys trigger on git push

---

## Dependency Graph

```
Phase W-A: Backend API
    ↓
    ├── Phase W-B: Frontend Shell (needs API to fetch data)
    │       ↓
    │   Phase W-C: Chat Interface (needs shell + API streaming)
    │       ↓
    └── Phase W-D: Polish & Deploy (needs everything working)
```

W-A must come first. W-B and W-C are sequential (shell before chat). W-D is last.

## Risk Areas

| Risk | Mitigation |
|------|------------|
| **Render cold start (~30s)** | Show "Server waking up..." message in frontend. Pre-warm with health check ping. |
| **SSE through Render proxy** | Verify Render doesn't buffer SSE responses. Set `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers. |
| **Demo book embedding cost** | Pre-compute embeddings once and bundle the seeded SQLite DB as a file, rather than re-embedding on every cold start. |
| **CORS configuration** | Lock down to Vercel domain in production. Allow `localhost` in dev. |
| **API key security** | Anthropic key is a server-side env var only. Never sent to the frontend. Rate-limit the chat endpoint to prevent abuse. |

## What This Demonstrates to Reviewers

| Skill | Evidence |
|-------|----------|
| **Python** | Domain layer, use cases, FastAPI API, async streaming |
| **TypeScript / React** | Vite, TanStack Query, SSE hooks, split-pane layout, component architecture |
| **UI/UX** | Book reader + chat split-pane, page sync, citation navigation, responsive design |
| **System design** | Three platforms sharing schema + prompts, thin API over domain use cases |
| **API design** | RESTful endpoints, SSE streaming, proper status codes |
| **DevOps** | Dockerized backend, CI/CD via git push, free-tier infrastructure |
| **AI/RAG** | Vector search, agentic retrieval, tool-use, prompt engineering, spoiler-free scoping |
| **DDD** | Same domain model across Python CLI, Swift app, and web API |
