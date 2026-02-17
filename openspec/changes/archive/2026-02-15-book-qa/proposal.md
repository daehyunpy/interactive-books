## Why

Phases 3-5 built the ingestion and retrieval pipeline: books are parsed, chunked, embedded, and searchable via vector similarity. But the pipeline stops at returning raw chunks — there's no LLM to turn retrieved context into a useful answer. Phase 6 closes the loop by adding the Q&A engine: embed the user's question, retrieve relevant chunks (using the existing search pipeline), assemble a prompt with context and citation instructions, and call an LLM to generate an answer with page references.

## What Changes

- Add `PromptMessage` domain model for representing LLM messages (role + content)
- Add `ChatProvider` protocol for LLM chat abstraction (`chat(messages) → str`)
- Add `LLMError` domain error type for LLM-specific failures (api_key_missing, api_call_failed, rate_limited, timeout)
- Implement Anthropic adapter as the default `ChatProvider` (using `anthropic` SDK)
- Create shared prompt templates in `shared/prompts/` (system prompt, query template, citation instructions)
- Build `AskBookUseCase` that orchestrates: search → build prompt → call LLM → return answer with citations
- Wire `cli ask <book-id> <question>` command

## Capabilities

### New Capabilities

- `chat-provider`: ChatProvider protocol, PromptMessage model, LLMError domain errors
- `anthropic-adapter`: Anthropic SDK implementation of ChatProvider
- `prompt-templates`: Shared prompt templates for system prompt, query assembly, and citation instructions
- `ask-pipeline`: AskBookUseCase orchestration and CLI ask command

### Modified Capabilities

- `repository-protocols`: Add ChatProvider protocol to protocols.py

## Impact

- **New dependency**: `anthropic` SDK added to `pyproject.toml`
- **New domain types**: `PromptMessage` dataclass, `LLMError` exception, `ChatProvider` protocol
- **New shared files**: `shared/prompts/system_prompt.md`, `shared/prompts/query_template.md`, `shared/prompts/citation_instructions.md`
- **New infra adapter**: `infra/llm/anthropic.py`
- **New use case**: `app/ask.py`
- **New CLI command**: `ask` in `main.py`
- **Existing code unchanged**: search pipeline, embedding pipeline, ingestion — all consumed as-is
