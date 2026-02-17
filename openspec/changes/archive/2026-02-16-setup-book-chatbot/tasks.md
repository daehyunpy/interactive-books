## 1. Schema & Domain Foundation

- [x] 1.1 Update `shared/schema/001_initial.sql`: add `conversations` table, rewrite `chat_messages` to use `conversation_id` FK, add `tool_result` to role CHECK constraint, add cascade from `books` to `conversations`
- [x] 1.2 Create `domain/conversation.py`: `Conversation` entity with `id`, `book_id`, `title`, `created_at`; enforce non-empty title invariant
- [x] 1.3 Modify `domain/chat.py`: add `TOOL_RESULT` to `MessageRole`, replace `book_id` with `conversation_id` on `ChatMessage`
- [x] 1.4 Create `domain/tool.py`: `ToolDefinition`, `ToolInvocation`, `ChatResponse` frozen dataclasses
- [x] 1.5 Modify `domain/prompt_message.py`: add optional `tool_use_id: str | None` and `tool_invocations: list[ToolInvocation] | None` fields
- [x] 1.6 Modify `domain/errors.py`: add `UNSUPPORTED_FEATURE` to `LLMErrorCode`
- [x] 1.7 Write tests for Conversation entity (title invariant, field access)
- [x] 1.8 Update tests for ChatMessage (conversation_id replaces book_id, TOOL_RESULT role)
- [x] 1.9 Write tests for ToolDefinition, ToolInvocation, ChatResponse value objects

## 2. Repository Protocols & SQLite Adapters

- [x] 2.1 Add `ConversationRepository` and `ChatMessageRepository` protocols to `domain/protocols.py`
- [x] 2.2 Extend `ChatProvider` protocol: add `chat_with_tools(messages, tools) -> ChatResponse` method
- [x] 2.3 Add `RetrievalStrategy` protocol to `domain/protocols.py`
- [x] 2.4 Add `ConversationContextStrategy` protocol to `domain/protocols.py`
- [x] 2.5 Create `infra/storage/conversation_repo.py`: SQLite `ConversationRepository` adapter
- [x] 2.6 Create `infra/storage/chat_message_repo.py`: SQLite `ChatMessageRepository` adapter (update existing if present)
- [x] 2.7 Write integration tests for `ConversationRepository` (save, get, get_by_book, delete cascade)
- [x] 2.8 Write integration tests for `ChatMessageRepository` (save, get_by_conversation, delete_by_conversation)

## 3. Prompt Templates

- [x] 3.1 Create `shared/prompts/conversation_system_prompt.md`: agentic system prompt with search_book tool instructions, citation rules, spoiler-free constraint
- [x] 3.2 Create `shared/prompts/reformulation_prompt.md`: instructions for producing self-contained search queries from conversation context

## 4. Anthropic Tool-Use Adapter

- [x] 4.1 Implement `chat_with_tools()` on Anthropic adapter in `infra/llm/anthropic.py`: map ToolDefinition to Anthropic tools format, handle tool_use content blocks in response, construct ChatResponse
- [x] 4.2 Write tests for Anthropic `chat_with_tools()`: tool invocation response, text-only response, API error wrapping

## 5. Retrieval & Context Strategies

- [x] 5.1 Create `infra/retrieval/tool_use.py`: `ToolUseRetrievalStrategy` — calls `chat_with_tools()`, handles tool invocations, loops with max-iterations guard
- [x] 5.2 Create `infra/retrieval/always_retrieve.py`: `AlwaysRetrieveStrategy` — reformulates query, always runs search, stuffs context, calls `chat()`
- [x] 5.3 Create `infra/context/full_history.py`: `FullHistoryStrategy` — returns last N messages from history
- [x] 5.4 Write tests for `ToolUseRetrievalStrategy` (tool invocation loop, max iterations, text-only response)
- [x] 5.5 Write tests for `AlwaysRetrieveStrategy` (reformulation, search execution, prompt assembly)
- [x] 5.6 Write tests for `FullHistoryStrategy` (capping, empty history, history shorter than cap)

## 6. Conversation Management Use Case

- [x] 6.1 Create `app/conversations.py`: create, list_by_book, rename, delete use cases
- [x] 6.2 Write tests for conversation management (create with auto-title, list by book, rename, delete cascade)

## 7. Chat Agent Use Case

- [x] 7.1 Create `app/chat.py`: `ChatWithBookUseCase` — agent loop orchestrator (load conversation, build context, call retrieval strategy, persist messages, return response)
- [x] 7.2 Delete `app/ask.py`: remove `AskBookUseCase` entirely
- [x] 7.3 Write tests for `ChatWithBookUseCase` (direct reply path, retrieve-then-reply path, conversation not found error, message persistence)

## 8. CLI Chat Command

- [x] 8.1 Remove `ask` command from `main.py`
- [x] 8.2 Add `chat <book-id>` command to `main.py`: conversation selection (list/create/resume), interactive REPL, `--verbose` flag for tool result display
- [x] 8.3 Wire all dependencies in the chat command callback: ChatProvider, SearchBooksUseCase, ConversationRepository, ChatMessageRepository, RetrievalStrategy, ConversationContextStrategy
- [x] 8.4 Write tests for CLI chat command (command registration, conversation selection, verbose output)

## 9. Cleanup & Verification

- [x] 9.1 Update existing tests that reference `ChatMessage.book_id` or `AskBookUseCase`
- [x] 9.2 Run `uv run ruff check .` and fix any lint errors
- [x] 9.3 Run `uv run pytest -x` and ensure all tests pass
- [x] 9.4 Run `uv run pyright` and fix any type errors
