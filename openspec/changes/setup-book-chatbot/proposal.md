## Why

The current Q&A system is stateless single-turn RAG: every question triggers a vector search, retrieves chunks, and sends them with the question to the LLM. There is no conversation memory, no session persistence, and no intelligence about when to retrieve. Users cannot ask follow-up questions, use pronouns referencing earlier turns, or resume a previous conversation. This is the same limitation every competitor (ChatPDF, Humata) has — and the gap our product brief identifies as a key differentiator.

Evolving to an agentic conversation system lets the agent maintain context, decide autonomously when retrieval is needed, and reformulate queries — turning a lookup tool into a reading companion.

## What Changes

- **Replace `AskBookUseCase` with `ChatWithBookUseCase`** — agent loop that builds conversation context, calls `chat_with_tools()`, executes tool if invoked, persists the turn, and returns the response
- **Add `Conversation` aggregate** — new domain entity (`id`, `book_id`, `title`, `created_at`) that owns `ChatMessage`s; multiple conversations per book, auto-titled from first message, user-renamable
- **Add `ChatMessage.conversation_id` FK, remove `ChatMessage.book_id`** — **BREAKING** (unreleased, no migration needed) — messages belong to a conversation, book reachable via `message → conversation → book`
- **Add `tool_result` to `MessageRole`** — new role for persisting tool invocation results (hidden in production, visible with `--verbose`)
- **Extend `ChatProvider` protocol** — add `chat_with_tools(messages, tools) → ChatResponse` method; add `ToolDefinition`, `ToolInvocation`, `ChatResponse` domain value objects
- **Add `RetrievalStrategy` protocol** — pluggable strategy for how the agent decides to retrieve (default: formal tool-use API; fallback: always-retrieve for Ollama)
- **Add `ConversationContextStrategy` protocol** — pluggable strategy for building conversation context (default: full history capped at N messages)
- **Add `ChatMessageRepository` protocol** — persistence for conversation messages
- **Add `ConversationRepository` protocol** — persistence for conversation aggregates
- **Replace CLI `ask` command with `chat` command** — **BREAKING** (unreleased) — interactive conversation mode with `--verbose` flag for tool result visibility
- **Add new prompt templates** — `conversation_system_prompt.md` (agent behavior + tool definitions) and `reformulation_prompt.md` (query rewriting with conversation context)
- **Add `conversations` table** — new SQL migration with `id`, `book_id` FK, `title`, `created_at`; rewrite `chat_messages` to use `conversation_id` FK

## Capabilities

### New Capabilities

- `conversation-management`: Conversation aggregate, repository, creation/listing/deletion, auto-titling, rename, cascade delete with book
- `chat-agent`: Agentic chat loop — `ChatWithBookUseCase`, tool-use integration, retrieval strategy, context strategy, prompt assembly, message persistence
- `chat-tool-use`: Tool-use protocol extensions — `chat_with_tools()` on `ChatProvider`, `ToolDefinition`/`ToolInvocation`/`ChatResponse` value objects, Anthropic adapter implementation
- `chat-cli`: Interactive `cli chat <book>` command replacing `cli ask`, conversation selection, `--verbose` tool result display

### Modified Capabilities

- `domain-models`: Add `Conversation` entity, add `conversation_id` to `ChatMessage`, remove `book_id` from `ChatMessage`, add `tool_result` to `MessageRole`
- `sql-schema`: Add `conversations` table, rewrite `chat_messages` FK from `book_id` to `conversation_id`, add `tool_result` to role CHECK constraint
- `chat-provider`: Extend `ChatProvider` protocol with `chat_with_tools()`, add `ToolDefinition`/`ToolInvocation`/`ChatResponse` to domain
- `prompt-templates`: Add `conversation_system_prompt.md` and `reformulation_prompt.md`
- `anthropic-adapter`: Implement `chat_with_tools()` using Anthropic's native tool-use API
- `ask-pipeline`: Replace entirely with `chat-agent` capability (AskBookUseCase → ChatWithBookUseCase)
- `cli-commands`: Remove `ask` command, add `chat` command with conversation selection
- `repository-protocols`: Add `ChatMessageRepository` and `ConversationRepository` protocols

## Impact

- **Domain layer**: New `Conversation` entity in `domain/conversation.py`; modified `ChatMessage` in `domain/chat.py`; new value objects in `domain/prompt_message.py` or new file; extended protocols in `domain/protocols.py`
- **Application layer**: New `app/chat.py` replacing `app/ask.py`; new `app/conversations.py` for CRUD
- **Infrastructure layer**: New `infra/storage/conversation_repo.py`; modified `infra/storage/chat_message_repo.py`; extended `infra/llm/anthropic.py` with tool-use
- **Schema**: New `shared/schema/003_add_conversations.sql` (or fold into `001_initial.sql` since unreleased)
- **Prompts**: New `shared/prompts/conversation_system_prompt.md` and `reformulation_prompt.md`
- **CLI**: Modified `main.py` — remove `ask` command group, add `chat` command group
- **Tests**: New tests for conversation domain, chat agent use case, tool-use, CLI chat command; modified tests for `ChatMessage` FK change
- **Ollama**: No tool-use support for now; falls back to always-retrieve via `RetrievalStrategy`
