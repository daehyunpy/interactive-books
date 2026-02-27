## 1 — Git LFS: add `.db` pattern to `.gitattributes`

- [x] Add `shared/fixtures/*.db filter=lfs diff=lfs merge=lfs -text` to `.gitattributes`
- [x] Verify with `git check-attr filter shared/fixtures/test.db` (should show `lfs`)

## 2 — Fixture: build and commit `1984_embedded.db`

- [x] Ingest `shared/fixtures/1984.pdf` into a local SQLite database using the CLI (`uv run interactive-books ingest`)
- [x] Embed the book (`uv run interactive-books embed <book_id>`) using OpenAI embeddings
- [x] Verify search works (`uv run interactive-books search <book_id> "Big Brother"`)
- [x] Inspect chunk data to pick a natural chapter boundary for `current_page` (note the page number)
- [x] Copy the `.db` file to `shared/fixtures/1984_embedded.db`
- [x] `git add` and commit the fixture (LFS should track it automatically)

> **Note:** Built programmatically (not via CLI) because LFS and OpenAI API
> were unavailable in the build environment. Uses deterministic hash-seeded
> fake embeddings (openai/1536). Chosen `current_page = 30` (chapter 3 boundary).
> Book ID: `f934486c-2c09-4325-9754-214fac6d74aa`

## 3 — Test utility: `judge_response()` in `tests/helpers/llm_judge.py`

- [x] Create `python/tests/helpers/llm_judge.py` with `judge_response(chat_provider: ChatProvider, actual: str, expected: str) -> bool`
- [x] Build the judge prompt: provide `actual` and `expected`, ask "Does this response match the expected behavior? Answer YES or NO, then explain."
- [x] Call `chat_provider.chat()` with the judge prompt
- [x] Parse the first word of the response as the verdict (`YES` → `True`, anything else → `False`)

## 4 — Integration tests: `test_spoiler_agent.py`

### Test list

| # | Test name | Question | Expected behavior (judge criteria) |
|---|-----------|----------|------------------------------------|
| 1 | `TestSpoilerPreventionViaSearch::test_agent_answers_from_early_content_without_spoilers` | "What is the setting of the story?" | Should describe Airstrip One, London, Oceania, telescreens, Victory Mansions — content from early chapters. Must NOT mention Room 101, Julia, Winston's arrest, thought reform, or "I love Big Brother." |
| 2 | `TestSpoilerPreventionViaKnowledge::test_agent_refuses_to_reveal_ending` | "How does the book end?" | Should refuse or say it cannot discuss content beyond the reader's current position. Must NOT mention Winston's arrest, Room 101, betrayal of Julia, "He loved Big Brother," or any Part Three events. |

### Implementation steps

- [x] Create `python/tests/app/test_spoiler_agent.py`
- [x] Add `pytestmark` with `pytest.mark.integration` and `skipif` for both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`
- [x] Add fixture: copy `shared/fixtures/1984_embedded.db` to `tmp_path`, open with `Database(path, enable_vec=True)`
- [x] Add fixture: set `book.current_page` to the chosen chapter boundary, save via `BookRepository`
- [x] Add fixture: create fresh `Conversation` per test via `ConversationRepository`
- [x] Add fixture: wire `ChatWithBookUseCase` with real Anthropic `ChatProvider`, real `ToolUseRetrievalStrategy`, real `FullHistoryContextStrategy`, real `SearchBooksUseCase` (with real OpenAI `EmbeddingProvider`), and real SQLite repositories
- [x] Write test #1 per test list
- [x] Write test #2 per test list
- [ ] Verify tests pass: `uv run pytest -m integration python/tests/app/test_spoiler_agent.py -v` (requires API keys — skipped in this env)

## 5 — Verify: lint and type checks

- [x] `uv run ruff check .` — no lint errors in new files
- [x] `uv run pyright` — no type errors in new files
