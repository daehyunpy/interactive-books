## 1. Domain Layer

- [x] 1.1 Create `ChatMessage` frozen dataclass in `domain/chat.py` with `role: str` and `content: str`
- [x] 1.2 Add `ChatProvider` protocol to `domain/protocols.py`: `model_name` property + `chat(messages: list[ChatMessage]) → str`
- [x] 1.3 Write domain tests for `ChatMessage` (creation, immutability)

## 2. Shared Prompt Templates

- [x] 2.1 Create `shared/prompts/system_prompt.md` — system prompt for book Q&A assistant
- [x] 2.2 Create `shared/prompts/query_template.md` — template with `{context}` and `{question}` placeholders
- [x] 2.3 Create `shared/prompts/citation_instructions.md` — page citation formatting rules

## 3. Infrastructure — Anthropic Adapter

- [x] 3.1 Add `anthropic` dependency to `pyproject.toml`
- [x] 3.2 Implement `ChatProvider` adapter in `infra/llm/anthropic.py` using Messages API with system message extraction
- [x] 3.3 Write tests for Anthropic adapter: successful call, system message extraction, API error handling, model name property

## 4. Application Layer — AskBookUseCase

- [x] 4.1 Create `AskBookUseCase` in `app/ask.py` with constructor injection of `ChatProvider`, `SearchBooksUseCase`, `prompts_dir`
- [x] 4.2 Implement `execute(book_id, question, top_k=5)`: search → load templates → assemble prompt → call LLM → return answer
- [x] 4.3 Implement context formatting: label each passage with page range, join with double newlines
- [x] 4.4 Handle edge cases: book not found, no embeddings, no search results, LLM failure
- [x] 4.5 Write unit tests for use case: successful Q&A, book not found, no embeddings, no results, context formatting, prompt assembly

## 5. CLI — Ask Command

- [x] 5.1 Wire `ask <book-id> <question>` command in `main.py` with `--top-k` option (default 5)
- [x] 5.2 Handle `ANTHROPIC_API_KEY` validation, print answer, handle errors

## 6. Verification

- [x] 6.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [x] 6.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
