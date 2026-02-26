## Why

The page-filtering spoiler prevention has two layers:

1. **Search layer** — `SearchBooksUseCase` filters chunks by `current_page` so the vector search never returns passages beyond the reader's position. This is already unit-tested in `tests/app/test_search.py`.
2. **Agent layer** — The LLM can answer from its own parametric knowledge, ignoring retrieval entirely. The system prompt says "Do not reveal content beyond the reader's current position," but nothing tests whether the agent actually obeys this instruction when the user asks a leading question.

The deleted `test_spoiler_prevention_integration.py` only tested layer 1 with a real PDF. It never tested the agent's actual response text. A user could ask "How does the book end?" and the agent could answer from general knowledge about 1984 without ever calling `search_book` — the search filter would never engage.

This change adds an **agent-level spoiler prevention test** that exercises the full `ChatWithBookUseCase` pipeline: user asks a spoiler-probing question → agent responds → we verify the response doesn't leak content beyond `current_page`.

## What Changes

- Add integration tests in `tests/app/test_spoiler_agent.py` that exercise `ChatWithBookUseCase` end-to-end with a controlled `ChatProvider` fake
- The fake `ChatProvider` simulates an LLM that either (a) calls `search_book` and synthesizes from results, or (b) attempts to answer from "parametric knowledge" — both scenarios are tested
- Assertions verify the agent response does NOT contain spoiler content (specific plot points, character names, or quotes from pages beyond `current_page`)
- Tests use synthetic book data (no LFS dependency) with known content at specific page ranges so assertions are deterministic
- No changes to production code — this is purely a test addition

## Capabilities

### New Capabilities
- `chat-agent` (testing): Agent-level spoiler prevention tests that verify `ChatWithBookUseCase` responses don't leak content beyond the reader's current page position

### Modified Capabilities
- None — no production code changes

## Impact

- **Test layer** (`tests/app/test_spoiler_agent.py`): New test file with agent-level spoiler prevention scenarios
- **Domain layer**: No changes
- **Application layer**: No changes
- **Infrastructure layer**: No changes
- **Shared fixtures**: May add synthetic book content fixtures for deterministic testing
