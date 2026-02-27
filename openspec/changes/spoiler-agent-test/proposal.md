## Why

The page-filtering spoiler prevention has two layers:

1. **Search layer** — `SearchBooksUseCase` filters chunks by `current_page` so the vector search never returns passages beyond the reader's position. This is already unit-tested in `tests/app/test_search.py`.
2. **Agent layer** — The LLM can answer from its own parametric knowledge, ignoring retrieval entirely. The system prompt says "Do not reveal content beyond the reader's current position," but nothing tests whether the agent actually obeys this instruction when the user asks a leading question.

The deleted `test_spoiler_prevention_integration.py` only tested layer 1 with a real PDF. It never tested the agent's actual response text. A user could ask "How does the book end?" and the agent could answer from general knowledge about 1984 without ever calling `search_book` — the search filter would never engage.

This change adds an **agent-level spoiler prevention test** that exercises the full `ChatWithBookUseCase` pipeline: user asks a spoiler-probing question → agent responds → we verify the response doesn't leak content beyond `current_page`.

## What Changes

- Add a generic `judge_response()` utility in `tests/helpers/llm_judge.py` — reusable LLM-as-judge for evaluating any prompt output against pre-decided expected behavior
- Add integration tests in `tests/app/test_spoiler_agent.py` that exercise `ChatWithBookUseCase` end-to-end with a real Anthropic `ChatProvider`
- Tests use a pre-built SQLite database (1984 with embeddings) stored in Git LFS — no re-ingestion or embedding API calls at test time
- Each test asks a spoiler-probing question, then uses `judge_response()` with a pre-decided expected-behavior description to evaluate the agent's response
- No changes to production code — this is purely a test addition

## Capabilities

### New Capabilities
- `chat-agent` (testing): Agent-level spoiler prevention tests that verify `ChatWithBookUseCase` responses don't leak content beyond the reader's current page position

### Modified Capabilities
- None — no production code changes

## Impact

- **Test utilities** (`tests/helpers/llm_judge.py`): New generic LLM-as-judge utility
- **Test layer** (`tests/app/test_spoiler_agent.py`): New test file with agent-level spoiler prevention scenarios
- **Shared fixtures** (`shared/fixtures/1984_embedded.db`): Pre-built SQLite DB in Git LFS
- **Domain layer**: No changes
- **Application layer**: No changes
- **Infrastructure layer**: No changes
