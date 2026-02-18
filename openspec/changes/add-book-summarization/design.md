## Context

The system currently stores book content as chunks with page ranges (`start_page`, `end_page`). Parsers for structured formats (PDF, EPUB, DOCX, Markdown) naturally produce page-aligned content where "pages" correspond to physical pages, chapters, or heading-delimited sections. The chunks preserve these page boundaries through word-to-page mapping in the chunker.

Users want to see a structural overview of the book before starting a conversation — section headings, what pages each section covers, and key statements from each section. This requires grouping chunks by their page ranges to reconstruct sections, then using the LLM to summarize each section and extract key statements.

## Goals / Non-Goals

**Goals:**

- Group chunks into logical sections based on page boundaries
- Use the LLM (`ChatProvider`) to summarize each section and extract key statements with page references
- Create a `summarize <book_id>` CLI command that outputs the structured summary
- Show the summary when starting a new conversation in the `chat` command
- Allow users to skip the summary with `--no-summary` flag on the `chat` command

**Non-Goals:**

- Extracting actual heading text from chunks (headings are mixed into chunk content; the LLM identifies them)
- Summarizing across multiple books
- Streaming summary generation (full generation, then display)

## Decisions

### 1. Section grouping strategy

**Decision:** Group chunks by contiguous page ranges. Consecutive chunks whose page ranges overlap or are adjacent form a section. Each section is represented by its combined page range and concatenated content.

**Rationale:** Chunks already carry `start_page` and `end_page`. Consecutive chunks from the same section of a book will have overlapping or adjacent page ranges (e.g., chunk 1 covers pages 1-2, chunk 2 covers pages 2-3 — these form one section). When there's a gap (chunk N ends at page 10, chunk N+1 starts at page 15), that signals a section break. This is a heuristic but works well for structured formats where parsers map headings to page boundaries.

**Alternatives considered:**

- Use heading detection regex on chunk content: fragile, format-dependent
- One section per page: too granular, doesn't capture logical structure
- Let the LLM decide section boundaries: expensive (requires sending all content), unreliable

### 2. Summarization approach

**Decision:** Send each section's concatenated content to the LLM with a structured prompt requesting: (a) a section title/heading, (b) a 2-3 sentence summary, and (c) 1-3 key statements with page numbers. Use `ChatProvider.chat()` (simple completion, no tool use needed).

**Rationale:** Per-section summarization keeps individual LLM calls manageable in token count. The structured prompt ensures consistent output format. Using the existing `ChatProvider` protocol means no new infrastructure.

**Alternatives considered:**

- Summarize the entire book in one call: may exceed context limits for large books
- Use embeddings for key statement extraction: overkill; the LLM is better at identifying significant statements

### 3. Output format

**Decision:** Return a list of `SectionSummary` value objects, each containing: `title: str`, `start_page: int`, `end_page: int`, `summary: str`, `key_statements: list[KeyStatement]` where `KeyStatement` has `statement: str` and `page: int`.

**Rationale:** Structured domain objects enable clean rendering in both CLI and future UI. The value objects are immutable and carry all information needed for display.

### 4. Integration with chat command

**Decision:** When a new conversation is created (no existing messages), automatically run summarization and display the result before the chat REPL starts. Add `--no-summary` flag to skip this. The summary is also injected as context into the system prompt for the first message.

**Rationale:** The summary orients the user for their conversation. Injecting it into the system prompt means the LLM also has structural awareness, improving response quality. The opt-out flag respects users who want to jump straight into chat.

### 5. Persistence

**Decision:** Persist section summaries in a `section_summaries` table with FK to `books`. Schema:

```sql
CREATE TABLE IF NOT EXISTS section_summaries (
    id TEXT PRIMARY KEY NOT NULL,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(title) > 0),
    start_page INTEGER NOT NULL CHECK (start_page >= 1),
    end_page INTEGER NOT NULL CHECK (end_page >= start_page),
    summary TEXT NOT NULL CHECK (length(summary) > 0),
    key_statements TEXT NOT NULL DEFAULT '[]',
    section_index INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
```

Key statements are stored as JSON in a TEXT column: `[{"statement": "...", "page": N}, ...]`.

**Rationale:** Summaries are expensive to generate (one LLM call per section). Persisting avoids re-generating on every chat start. The `summarize` command generates and persists; subsequent calls return cached results unless `--regenerate` is passed. The `section_summaries` table uses CASCADE delete so summaries are cleaned up when a book is deleted.

A `SummaryRepository` protocol in the domain layer provides `save_all(book_id, summaries)`, `get_by_book(book_id)`, and `delete_by_book(book_id)`. The infra adapter follows the same patterns as other repositories.

**Alternatives considered:**

- Store as a single JSON blob on the `books` table: loses queryability, schema validation
- Separate `key_statements` table: over-normalized for read-heavy, write-once data

### 6. Token budget for summarization

**Decision:** Cap each section's content at 6000 tokens before sending to the LLM. If a section exceeds this, truncate with a note. Cap total sections at 30 to avoid excessive API calls.

**Rationale:** Prevents runaway costs on very large books. 6000 tokens per section is enough for a good summary. 30 sections covers most book structures. These are named constants (`MAX_SECTION_TOKENS`, `MAX_SECTIONS`).

## Risks / Trade-offs

**[Trade-off] LLM cost per summarization** - Each summarization requires one LLM call per section. A book with 20 sections means 20 API calls. This is acceptable for on-demand use but argues against running it automatically on every chat start for returning conversations (hence only on new conversations).

**[Trade-off] JSON key_statements column** - Storing key statements as JSON in a TEXT column trades queryability for simplicity. Since key statements are always read/written as a group with their parent section, this is acceptable.

**[Risk] Section grouping heuristic** - The contiguous-page-range grouping may not perfectly match the book's actual structure. For formats like TXT where page numbers are estimated, sections may be less meaningful. Mitigation: the LLM identifies headings from content, compensating for imperfect grouping.
