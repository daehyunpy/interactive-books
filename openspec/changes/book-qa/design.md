## Context

Phases 3-5 built the complete ingestion and retrieval pipeline: books are parsed into chunks, embedded via OpenAI, and searchable via sqlite-vec KNN. The `SearchBooksUseCase` returns `SearchResult` objects with chunk content, page ranges, and distance scores. Phase 6 adds the final piece: an LLM that takes retrieved context and a user question and produces an answer with page citations.

The technical design specifies a `ChatProvider` protocol abstraction with Anthropic as the default implementation, shared prompt templates in `shared/prompts/`, and a `cli ask` command.

`LLMError` and `LLMErrorCode` already exist in `domain/errors.py` (scaffolded in Phase 1).

## Goals / Non-Goals

**Goals:**

- Add `ChatMessage` domain model for LLM message representation (role + content)
- Add `ChatProvider` protocol for LLM chat abstraction
- Implement Anthropic adapter as the default ChatProvider
- Create shared prompt templates (system prompt, query template, citation instructions)
- Build `AskBookUseCase` that orchestrates search → prompt assembly → LLM call → answer
- Wire `cli ask <book-id> <question>` command
- Return answers as plain text with page citations (e.g., "As mentioned on p.42...")

**Non-Goals:**

- Streaming responses — return full text for v1, streaming is Phase 7 polish
- Chat history / multi-turn conversation — single question-answer for v1
- OpenAI or Ollama chat adapters — Anthropic only for now, others added later
- Prompt optimization or tuning — functional templates first
- Token counting or context window management — trust reasonable defaults for v1

## Decisions

### 1. ChatMessage as a frozen dataclass

**Decision:** Define `ChatMessage` in `domain/chat.py` as a frozen dataclass with `role: str` and `content: str`. The `role` is one of `"system"`, `"user"`, `"assistant"`.

**Rationale:** The technical design already specifies `chat.py` in the directory layout. A frozen dataclass matches the pattern of other domain value objects (`EmbeddingVector`, `SearchResult`, `ChunkData`). Role is a plain string rather than an enum because LLM providers may add roles and we don't want to update an enum for every provider quirk.

**Alternatives considered:**

- Enum for role: too rigid, different providers have slightly different role sets
- Dict/tuple: loses type safety and readability

### 2. ChatProvider protocol — synchronous, non-streaming

**Decision:** `ChatProvider` protocol with a single method: `chat(messages: list[ChatMessage]) → str`. Returns the full response as a string. Has a `model_name` property.

**Rationale:** For the CLI, synchronous is simplest and sufficient. Streaming adds complexity (generators, partial responses) that isn't needed until the iOS/macOS app (Phase 8). The protocol can be extended with a `stream` method later without breaking existing code.

**Alternatives considered:**

- `chat() → Iterator[str]` for streaming: premature for CLI-only usage
- `complete(prompt: str) → str` without message structure: loses multi-message capability needed for system + user messages
- Separate `SystemPrompt` and `UserQuery` types: over-engineering for what is essentially a message list

### 3. Anthropic adapter using Messages API

**Decision:** Implement `ChatProvider` in `infra/llm/anthropic.py` using the `anthropic` Python SDK's `messages.create()` API. Default model: `claude-sonnet-4-5-20250514`. System message is passed via the `system` parameter (not as a message).

**Rationale:** Anthropic's Messages API expects the system prompt as a separate parameter, not in the messages array. The adapter handles this translation — callers always use `ChatMessage(role="system", ...)` and the adapter extracts it. Claude Sonnet 4.5 balances quality and speed for a CLI tool.

**Alternatives considered:**

- Claude Opus: higher quality but slower and more expensive for iterative CLI use
- Claude Haiku: faster but may produce lower quality citations
- Pass system prompt as a separate parameter in the protocol: leaks provider-specific concerns into the domain

### 4. Prompt templates in shared/prompts/

**Decision:** Create three markdown files in `shared/prompts/`:

- `system_prompt.md` — base system prompt establishing the assistant's role and constraints
- `query_template.md` — template for assembling user query with retrieved context
- `citation_instructions.md` — instructions for how to cite pages in answers

The use case reads these files and assembles the final prompt. Templates use `{variable}` placeholders.

**Rationale:** The technical design mandates `shared/prompts/` for cross-platform consistency. Markdown files are human-readable and easy to edit. Keeping them as separate files (not embedded in code) means prompt changes don't require code changes.

**Alternatives considered:**

- Inline prompts in Python code: harder to maintain, can't share with Swift
- Single combined template: less modular, harder to iterate on parts independently
- Jinja2 templates: adds a dependency for simple string formatting

### 5. AskBookUseCase orchestrates the full pipeline

**Decision:** `AskBookUseCase` in `app/ask.py` accepts `ChatProvider` and `SearchBooksUseCase` via constructor injection (plus `prompts_dir: Path`). The `execute(book_id, question, top_k=5)` method:

1. Calls `SearchBooksUseCase.execute()` to get relevant chunks
2. Loads prompt templates from `prompts_dir`
3. Builds the message list: system prompt + user query with embedded context
4. Calls `ChatProvider.chat()` to get the answer
5. Returns the answer string

**Rationale:** Injecting `SearchBooksUseCase` directly (instead of its 4 sub-dependencies) keeps `AskBookUseCase` focused on prompt assembly + LLM call. Book validation (not found, no embeddings) is handled by the search use case. This reduces the constructor from 6 dependencies to 3.

**Alternatives considered:**

- Inject raw dependencies (EmbeddingProvider, BookRepository, etc.): 6 constructor params, duplicates validation logic
- Separate PromptBuilder class: over-engineering for v1, the assembly is ~10 lines
- Return a structured `Answer` object: premature — plain string is sufficient for CLI

### 6. Prompt template path resolution

**Decision:** The `AskBookUseCase` accepts a `prompts_dir: Path` parameter (defaulting to `shared/prompts/` relative to the project root). This keeps the use case testable — tests pass a temp directory with test prompts.

**Rationale:** Hardcoding the path would make unit tests depend on the real prompt files. A parameter allows injection of test prompts. The CLI command resolves the default path.

## Risks / Trade-offs

**[Risk] Anthropic API rate limiting** → Mitigation: `LLMError` with `RATE_LIMITED` code. The CLI just reports the error. Retry logic can be added in Phase 7 polish.

**[Risk] Context too large for model window** → Mitigation: top_k=5 with ~500-1000 token chunks means ~2500-5000 tokens of context. Claude Sonnet's 200k window handles this easily. Not a concern for v1.

**[Risk] Poor citation quality** → Mitigation: Explicit citation instructions in the prompt template. Can be iterated on without code changes.

**[Trade-off] Non-streaming for v1** → Users wait for the full response. Acceptable for a CLI debugging tool. Streaming will be added for the app in Phase 7/8.

**[Trade-off] Loading prompt files on every call** → Negligible for CLI use. The app can cache templates if needed.
