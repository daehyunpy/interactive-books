# ask-pipeline

Delta spec for the ask pipeline. The entire `AskBookUseCase` is replaced by `ChatWithBookUseCase` in the `chat-agent` capability. The CLI `ask` command is removed in favor of `chat` (see `cli-commands` spec).

## REMOVED Requirements

### AP-1: AskBookUseCase orchestrates question answering

**Reason:** `AskBookUseCase` is replaced by `ChatWithBookUseCase` (see `chat-agent` spec, requirement CA-1). The new use case provides agentic conversation with tool-use, conversation context, and message persistence -- a superset of what `AskBookUseCase` provided.

**Migration:** All code that calls `AskBookUseCase.execute(book_id, question)` SHALL be replaced with `ChatWithBookUseCase.execute(conversation_id, user_message)`. Callers must first create or select a `Conversation` and pass its `conversation_id` instead of `book_id`. The `ChatWithBookUseCase` handles retrieval internally via the agent loop rather than always calling search.

### AP-2: Prompt assembly uses shared templates

**Reason:** Prompt assembly is replaced by the conversation system prompt and context strategy in `ChatWithBookUseCase`. The new prompt assembly uses `conversation_system_prompt.md` (see `prompt-templates` spec, PT-4) instead of `system_prompt.md` + `query_template.md` + `citation_instructions.md`. Context is built by `ConversationContextStrategy` (see `chat-agent` spec, CA-5/CA-6).

**Migration:** The existing `system_prompt.md`, `query_template.md`, and `citation_instructions.md` templates remain available for potential future single-turn use cases but are no longer used by the primary chat pipeline. The new `conversation_system_prompt.md` subsumes their functionality for agentic conversation.

### AP-3: CLI ask command wires the Q&A pipeline

**Reason:** The `ask` CLI command is replaced by the `chat` command (see `cli-commands` spec). The `chat` command provides an interactive REPL with conversation persistence, tool-use, and verbose mode.

**Migration:** Remove the `ask` command from `main.py`. Users use `cli chat <book-id>` instead. See `chat-cli` spec for the replacement command's full specification.
