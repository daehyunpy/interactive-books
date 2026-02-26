# chat-agent (delta)

Agent-level spoiler prevention integration tests and generic LLM-as-judge test utility.

## Requirements

### CA-10: Generic LLM-as-judge test utility

The test infrastructure SHALL provide a `judge_response` function in `tests/helpers/llm_judge.py` with the signature:

- `judge_response(chat_provider: ChatProvider, actual: str, expected: str) -> bool`

The function is domain-agnostic. It sends a single `chat()` call with a judge prompt containing the `actual` response and the `expected` behavior description. It parses the first word of the judge's reply as the verdict (`YES` = match, `NO` = mismatch) and returns `True` when the verdict is `YES`.

#### Scenario: Response matches expected behavior

- **WHEN** `judge_response` is called with an `actual` response that satisfies the `expected` criteria
- **THEN** the function returns `True`

#### Scenario: Response violates expected behavior

- **WHEN** `judge_response` is called with an `actual` response that violates the `expected` criteria
- **THEN** the function returns `False`

### CA-11: Spoiler prevention integration test — search-bounded response

An integration test SHALL exercise `ChatWithBookUseCase` end-to-end with a pre-built SQLite fixture database (`shared/fixtures/1984_embedded.db`) containing *1984* with chunks and embeddings. The test:

1. Copies the fixture DB to `tmp_path`
2. Opens it with `Database(path, enable_vec=True)`
3. Sets `book.current_page` to a natural chapter boundary
4. Creates a fresh `Conversation` for the book
5. Wires `ChatWithBookUseCase` with real `ChatProvider` (Anthropic), real `ToolUseRetrievalStrategy`, real `FullHistoryContextStrategy`, real `SearchBooksUseCase`, and real SQLite repositories
6. Calls `execute(conversation_id, question)` with a question about early-book content
7. Evaluates the response with `judge_response` using a pre-decided expected-behavior description
8. Asserts the judge returns `True`

The test is marked `@pytest.mark.integration` and is skipped when `ANTHROPIC_API_KEY` is not set.

#### Scenario: Agent answers from early-book content without spoilers

- **WHEN** the reader's `current_page` is set to a chapter boundary and the user asks about content from early pages
- **THEN** the agent responds using retrieved passages from within the page boundary, and the judge confirms the response does not leak content beyond `current_page`

### CA-12: Spoiler prevention integration test — parametric knowledge refusal

An integration test SHALL exercise the same pipeline as CA-11 but with a question that probes for late-book content (e.g., "How does the book end?"). Because `current_page` restricts search results to early pages, the search tool returns no relevant passages for the ending. The test verifies the agent refuses to answer from parametric knowledge.

#### Scenario: Agent refuses to reveal late-book content

- **WHEN** the reader's `current_page` is set to an early chapter boundary and the user asks about the book's ending
- **THEN** the agent does not reveal plot events beyond the reader's position, and the judge confirms the response contains no spoilers
