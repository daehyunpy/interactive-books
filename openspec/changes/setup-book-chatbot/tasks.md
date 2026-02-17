## 1. Schema & Domain Foundation

- [ ] 1.1 Update `shared/schema/001_initial.sql`: add `conversations` table, rewrite `chat_messages` to use `conversation_id` FK, add `tool_result` to role CHECK constraint, add cascade from `books` to `conversations`
- [ ] 1.2 Create `domain/conversation.py`: `Conversation` entity with `id`, `book_id`, `title`, `created_at`; enforce non-empty title invariant
- [ ] 1.3 Modify `domain/chat.py`: add `TOOL_RESULT` to `MessageRole`, replace `book_id` with `conversation_id` on `ChatMessage`
- [ ] 1.4 Create `domain/tool.py`: `ToolDefinition`, `ToolInvocation`, `ChatResponse` frozen dataclasses
- [ ] 1.5 Modify `domain/prompt_message.py`: add optional `tool_use_id: str | None` and `tool_invocations: list[ToolInvocation] | None` fields
- [ ] 1.6 Modify `domain/errors.py`: add `UNSUPPORTED_FEATURE` to `LLMErrorCode`
- [ ] 1.7 Write tests for Conversation entity (title invariant, field access)
- [ ] 1.8 Update tests for ChatMessage (conversation_id replaces book_id, TOOL_RESULT role)
- [ ] 1.9 Write tests for ToolDefinition, ToolInvocation, ChatResponse value objects

## 2. Repository Protocols & SQLite Adapters

- [ ] 2.1 Add `ConversationRepository` and `ChatMessageRepository` protocols to `domain/protocols.py`
- [ ] 2.2 Extend `ChatProvider` protocol: add `chat_with_tools(messages, tools) -> ChatResponse` method
- [ ] 2.3 Add `RetrievalStrategy` protocol to `domain/protocols.py`
- [ ] 2.4 Add `ConversationContextStrategy` protocol to `domain/protocols.py`
- [ ] 2.5 Create `infra/storage/conversation_repo.py`: SQLite `ConversationRepository` adapter
- [ ] 2.6 Create `infra/storage/chat_message_repo.py`: SQLite `ChatMessageRepository` adapter (update existing if present)
- [ ] 2.7 Write integration tests for `ConversationRepository` (save, get, get_by_book, delete cascade)
- [ ] 2.8 Write integration tests for `ChatMessageRepository` (save, get_by_conversation, delete_by_conversation)

## 3. Prompt Templates

- [ ] 3.1 Create `shared/prompts/conversation_system_prompt.md`: agentic system prompt with search_book tool instructions, citation rules, spoiler-free constraint
- [ ] 3.2 Create `shared/prompts/reformulation_prompt.md`: instructions for producing self-contained search queries from conversation context

## 4. Anthropic Tool-Use Adapter

- [ ] 4.1 Implement `chat_with_tools()` on Anthropic adapter in `infra/llm/anthropic.py`: map ToolDefinition to Anthropic tools format, handle tool_use content blocks in response, construct ChatResponse
- [ ] 4.2 Write tests for Anthropic `chat_with_tools()`: tool invocation response, text-only response, API error wrapping

## 5. Retrieval & Context Strategies

- [ ] 5.1 Create `infra/retrieval/tool_use.py`: `ToolUseRetrievalStrategy` — calls `chat_with_tools()`, handles tool invocations, loops with max-iterations guard
- [ ] 5.2 Create `infra/retrieval/always_retrieve.py`: `AlwaysRetrieveStrategy` — reformulates query, always runs search, stuffs context, calls `chat()`
- [ ] 5.3 Create `infra/context/full_history.py`: `FullHistoryStrategy` — returns last N messages from history
- [ ] 5.4 Write tests for `ToolUseRetrievalStrategy` (tool invocation loop, max iterations, text-only response)
- [ ] 5.5 Write tests for `AlwaysRetrieveStrategy` (reformulation, search execution, prompt assembly)
- [ ] 5.6 Write tests for `FullHistoryStrategy` (capping, empty history, history shorter than cap)

## 6. Conversation Management Use Case

- [ ] 6.1 Create `app/conversations.py`: create, list_by_book, rename, delete use cases
- [ ] 6.2 Write tests for conversation management (create with auto-title, list by book, rename, delete cascade)

## 7. Chat Agent Use Case

- [ ] 7.1 Create `app/chat.py`: `ChatWithBookUseCase` — agent loop orchestrator (load conversation, build context, call retrieval strategy, persist messages, return response)
- [ ] 7.2 Delete `app/ask.py`: remove `AskBookUseCase` entirely
- [ ] 7.3 Write tests for `ChatWithBookUseCase` (direct reply path, retrieve-then-reply path, conversation not found error, message persistence)

## 8. CLI Chat Command

- [ ] 8.1 Remove `ask` command from `main.py`
- [ ] 8.2 Add `chat <book-id>` command to `main.py`: conversation selection (list/create/resume), interactive REPL, `--verbose` flag for tool result display
- [ ] 8.3 Wire all dependencies in the chat command callback: ChatProvider, SearchBooksUseCase, ConversationRepository, ChatMessageRepository, RetrievalStrategy, ConversationContextStrategy
- [ ] 8.4 Write tests for CLI chat command (command registration, conversation selection, verbose output)

## 9. Cleanup & Verification

- [ ] 9.1 Update existing tests that reference `ChatMessage.book_id` or `AskBookUseCase`
- [ ] 9.2 Run `uv run ruff check .` and fix any lint errors
- [ ] 9.3 Run `uv run pytest -x` and ensure all tests pass
- [ ] 9.4 Run `uv run pyright` and fix any type errors
