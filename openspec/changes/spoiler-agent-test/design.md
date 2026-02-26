## Context

Spoiler prevention in Interactive Books has two layers:

1. **Search layer** — `SearchBooksUseCase` filters chunks by `current_page`, so vector search never returns passages from future pages. This is unit-tested in `tests/app/test_search.py` (class `TestPageFiltering`).
2. **Agent layer** — The system prompt in `conversation_system_prompt.md` instructs the LLM: "Do not reveal or discuss content from pages beyond the reader's current position." But if the user asks about a well-known book's ending, the LLM could answer from parametric (training) knowledge, bypassing search entirely.

The deleted `test_spoiler_prevention_integration.py` tested layer 1 only — it verified that search results excluded late-page chunks. It never tested the LLM's actual response text. This change adds agent-level tests that exercise the full `ChatWithBookUseCase` pipeline with a **real LLM** and evaluate responses with an **LLM-as-judge**.

The existing test infrastructure uses in-memory SQLite (`Database(":memory:")`) with fake repositories for unit tests, and real `Database` + `sqlite_vec` for integration tests (`enable_vec=True`). The `ChatWithBookUseCase` requires: `ChatProvider`, `RetrievalStrategy`, `ConversationContextStrategy`, `SearchBooksUseCase`, `ConversationRepository`, `ChatMessageRepository`, and `prompts_dir`.

## Goals / Non-Goals

**Goals:**
- Test the agent's actual response text for spoiler leakage when `current_page` restricts the reader's position
- Use a pre-built SQLite database (stored in Git LFS) containing a well-known book with chunks and embeddings, so tests don't need to re-ingest or call embedding APIs
- Use a real Anthropic `ChatProvider` to exercise the full agent loop (system prompt + tool use + response)
- Use a second LLM call (judge) to evaluate whether the response leaks content beyond `current_page`
- Mark tests with `@pytest.mark.integration` so they only run when API keys are available

**Non-Goals:**
- Re-testing the search-level page filtering (already covered in `test_search.py`)
- Testing with every supported book format — one well-known book is sufficient
- Making these tests deterministic — LLM responses are inherently non-deterministic; the judge pattern tolerates this
- Testing prompt injection attacks or adversarial jailbreaks
- Modifying any production code

## Decisions

### 1. Pre-built SQLite database in Git LFS

**Decision:** Store a pre-populated `.db` file in `shared/fixtures/` tracked by Git LFS. The DB contains one well-known book (e.g., *1984*) with chunks and embeddings already computed.

**Rationale:** The test needs real embeddings to exercise the full search pipeline. Computing embeddings at test time would require an API key and add minutes to test setup. A pre-built DB makes the test self-contained — just open the file and go. Git LFS is already configured for `shared/fixtures/` files.

**DB setup details:**
- Copy the LFS `.db` file to a temp directory at test start (avoids modifying the fixture)
- Open with `Database(tmp_copy, enable_vec=True)` and skip migrations (already applied)
- The book's `current_page` will be set to a natural chapter boundary from the chunk data

**Fixture creation:** Build the DB manually (ingest 1984, embed, verify), then commit the `.db` file to Git LFS. No build script — the DB is a static fixture that rarely needs regeneration.

**Trade-off:** The DB is coupled to a specific embedding provider and dimension. If the provider changes, the fixture must be manually rebuilt. This is acceptable because provider changes are rare and the rebuild process is straightforward (ingest → embed → copy `.db`).

### 2. Real Anthropic ChatProvider for the agent

**Decision:** Use the real `infra.llm.anthropic.ChatProvider` with a live API key. The `ToolUseRetrievalStrategy` is also real — the full agent loop runs end-to-end.

**Rationale:** The whole point is to test the LLM's behavior. A fake would only test orchestration (already covered in `test_chat.py`). The real provider exercises the system prompt, tool-use decisions, and natural language responses.

**Test marker:** `@pytest.mark.integration` — skipped when `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is not set. Both are required: Anthropic for chat, OpenAI for query embedding at search time.

### 3. Generic LLM-as-judge for response evaluation

**Decision:** A reusable `judge_response(chat_provider, actual, expected) → bool` function in `tests/helpers/llm_judge.py`. It takes the agent's actual response and a pre-decided expected-behavior description, then asks the LLM whether the actual response matches. Domain-agnostic — knows nothing about books, pages, or spoilers.

**Rationale:** String matching is brittle — the LLM can paraphrase or allude. An LLM judge understands semantic meaning. Making the judge generic means it can be reused for any prompt evaluation (not just spoiler tests).

**Interface:**
- `actual: str` — the response from the agent under test
- `expected: str` — a plain-English description of what the correct response should (or should not) contain, written by the test author
- Returns `True` if the response matches the expected criteria, `False` otherwise
- The judge prompt asks: "Does this response match the expected behavior? Answer YES or NO, then explain."
- Parse the first word for the verdict

**Example usage in a spoiler test:**
```python
assert judge_response(
    provider,
    actual=response,
    expected="The response should refuse to discuss how the book ends. "
             "It must NOT mention Room 101, Winston's betrayal of Julia, "
             "or his acceptance of Big Brother.",
)
```

**Location:** `python/tests/helpers/llm_judge.py` — shared test utility, reusable across any test that needs to evaluate prompt output.

**Trade-off:** This adds a second API call per test case and introduces its own non-determinism. However, the judge task is much simpler (binary classification) than the chat task, so it should be reliable. If flakiness occurs, we can run the judge multiple times and majority-vote.

### 4. Test structure: two scenario classes

**Decision:** Organize tests into two classes:
- `TestSpoilerPreventionViaSearch` — User asks about content the LLM *should* find via search (content exists in early pages). Verifies the agent uses `search_book` and the response stays within bounds.
- `TestSpoilerPreventionViaKnowledge` — User asks a leading question about late-book content (e.g., "How does the book end?"). The search returns no results (page-filtered), and we verify the agent doesn't answer from parametric knowledge.

**Test count:** 2–3 focused scenarios total — one per spoiler vector, plus an optional edge case. Keeps API cost and runtime low while covering both leak paths.

**Rationale:** These are the two spoiler leak vectors. The first tests that the search pipeline + agent work together correctly. The second tests that the system prompt prevents knowledge leakage when search can't help.

### 5. Conversation setup per test

**Decision:** Each test creates a fresh conversation in the pre-built DB. The book already exists; only a `Conversation` row and the `ChatWithBookUseCase` call are new per test.

**Rationale:** Conversations are lightweight (just an ID, book_id, and title). Creating them per test avoids cross-test contamination in conversation history while reusing the expensive book/chunk/embedding data.

## Architecture

```
Test setup:
  shared/fixtures/1984_embedded.db  (Git LFS)
       │
       ▼
  tmp_path copy → Database(enable_vec=True)
       │
       ├── BookRepository ──── (pre-populated book with current_page set)
       ├── ChunkRepository ─── (pre-populated chunks spanning all pages)
       ├── EmbeddingRepository ─ (pre-populated embeddings)
       ├── ConversationRepository ─ (fresh conversation per test)
       └── ChatMessageRepository ── (empty per test)
       │
       ▼
  ChatWithBookUseCase
       ├── ChatProvider: real Anthropic (ANTHROPIC_API_KEY)
       ├── RetrievalStrategy: real ToolUseRetrievalStrategy
       ├── ContextStrategy: real FullHistoryContextStrategy
       ├── SearchBooksUseCase: real (using real repos above)
       └── prompts_dir: shared/prompts/

Test flow:
  1. Copy fixture DB → tmp_path
  2. Open Database, set book.current_page = chapter boundary
  3. Create fresh Conversation
  4. Call use_case.execute(conversation_id, spoiler_question)
  5. judge_response(provider, actual=response, expected=pre_decided_criteria)
  6. Assert judge returns True
```

**File layout:**
- `python/tests/helpers/llm_judge.py` — generic `judge_response()` utility, reusable for any prompt evaluation
- `python/tests/app/test_spoiler_agent.py` — test file with both scenario classes
- `shared/fixtures/1984_embedded.db` — pre-built SQLite DB in Git LFS (manually built, no generation script)
