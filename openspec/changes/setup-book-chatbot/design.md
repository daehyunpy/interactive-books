# Design: setup-book-chatbot

## Context

The Q&A system today is stateless single-turn RAG. `AskBookUseCase` receives a question, always runs a vector search, stuffs the top-k chunks into a prompt, and returns the LLM response. There is no conversation history, no session persistence, and no intelligence about whether retrieval is even necessary. `ChatMessage` exists in the domain but has a `book_id` FK and is never actually persisted or used in the pipeline. The CLI exposes this as `cli ask <book> <question>`.

This change replaces the stateless pipeline with an agentic conversation system. See `proposal.md` for motivation and the full list of what changes.

## Goals / Non-Goals

**Goals:**

- Multi-turn conversations with persistent history per book
- Agent-driven retrieval: the LLM decides when to search via tool-use, not every turn
- Query reformulation: the agent produces self-contained search queries from conversational context (resolving anaphora, ellipsis)
- Pluggable retrieval and context strategies behind protocol abstractions
- Clean domain model: `Conversation` aggregate owns `ChatMessage`s; no `book_id` on messages
- Replace `cli ask` with `cli chat` — interactive REPL with conversation selection

**Non-Goals:**

- Ollama tool-use support (deferred; falls back to always-retrieve)
- Streaming responses (future enhancement)
- Multi-book conversations (one book per conversation for now)
- OpenAI adapter for `chat_with_tools()` (Anthropic-only for MVP; OpenAI added later)
- Sliding-window or summary-based context strategies (full-history-capped is the only implementation)

## Decisions

### 1. Domain model: Conversation aggregate

`Conversation` becomes a second aggregate root alongside `Book`.

```
Conversation
  id: str                  # UUID
  book_id: str             # FK to Book
  title: str               # auto-generated from first user message, renamable
  created_at: datetime

ChatMessage
  id: str                  # UUID
  conversation_id: str     # FK to Conversation (replaces book_id)
  role: MessageRole        # user | assistant | tool_result
  content: str
  created_at: datetime
```

`ChatMessage.book_id` is removed. The book is reachable via `message.conversation_id -> conversation.book_id`. This is a breaking schema change but acceptable since `chat_messages` is unused in the released codebase.

`MessageRole` gains `TOOL_RESULT = "tool_result"` for persisted tool invocation results. The SQL CHECK constraint on `chat_messages.role` must be updated to include `'tool_result'`.

**Rationale:** Messages belong to conversations, not books. The indirect path through the conversation is the correct domain relationship and avoids a denormalized `book_id` on every message.

### 2. Schema change strategy

Since neither `chat_messages` nor the conversation model have shipped, fold the changes directly into `001_initial.sql`:

- Add `conversations` table (`id`, `book_id` FK, `title`, `created_at`)
- Rewrite `chat_messages`: replace `book_id` FK with `conversation_id` FK to `conversations`, add `'tool_result'` to the role CHECK, index on `conversation_id`
- Add CASCADE from `conversations` to `chat_messages`, and from `books` to `conversations`

No migration file is needed. This is a pre-release schema rewrite.

**Rationale:** Adding a migration for a table nobody uses yet would create unnecessary complexity. A clean rewrite of `001_initial.sql` is simpler and produces the same end state.

### 3. Tool-use protocol extension on ChatProvider

`ChatProvider` gains a second method:

```python
class ChatProvider(Protocol):
    @property
    def model_name(self) -> str: ...
    def chat(self, messages: list[PromptMessage]) -> str: ...
    def chat_with_tools(
        self,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
    ) -> ChatResponse: ...
```

New domain value objects:

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, object]   # JSON Schema

@dataclass(frozen=True)
class ToolInvocation:
    tool_name: str
    tool_use_id: str
    arguments: dict[str, object]

@dataclass(frozen=True)
class ChatResponse:
    text: str | None                       # None when the response is purely a tool call
    tool_invocations: list[ToolInvocation]  # empty when the response is purely text
```

`chat()` remains for backward compatibility (search, embed, and any non-agentic use). `chat_with_tools()` is the agentic entry point. The Anthropic adapter implements it using the native `tools` parameter on `messages.create()`.

**Rationale:** Extending the existing protocol (rather than creating a separate `AgenticChatProvider`) keeps the provider abstraction unified. Providers that do not support tool-use raise `LLMError(UNSUPPORTED_FEATURE)` from `chat_with_tools()`. The `RetrievalStrategy` abstraction handles the fallback path.

### 4. PromptMessage extension for tool-use

`PromptMessage` currently has `role: str` and `content: str`. Tool-use requires richer message types:

- **Tool result messages** need a `tool_use_id` to correlate with the invocation
- **Assistant messages with tool calls** need to carry `ToolInvocation` data

Extend `PromptMessage`:

```python
@dataclass(frozen=True)
class PromptMessage:
    role: str
    content: str
    tool_use_id: str | None = None                    # set on tool_result messages
    tool_invocations: list[ToolInvocation] | None = None  # set on assistant messages with tool calls
```

This keeps `PromptMessage` as the single message type flowing through the system. The Anthropic adapter maps these fields to the API's expected format (content blocks with `type: "tool_use"` and `type: "tool_result"`).

**Rationale:** A single message type is simpler than a union of message subtypes. The optional fields are only populated for tool-use turns and are `None` for regular messages.

### 5. RetrievalStrategy protocol

```python
class RetrievalStrategy(Protocol):
    def execute(
        self,
        chat_provider: ChatProvider,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        search_fn: Callable[[str], list[SearchResult]],
    ) -> tuple[str, list[ChatMessage]]:
        """Returns (assistant_response_text, new_messages_to_persist)."""
        ...
```

Two implementations:

- **`ToolUseRetrievalStrategy`** (default): Calls `chat_with_tools()`. If the LLM returns tool invocations, executes the search, appends results as `tool_result` messages, calls the LLM again. Loops until the LLM responds with text only (with a max-iterations guard).
- **`AlwaysRetrieveStrategy`** (fallback): Reformulates the query from conversation context, always runs search, stuffs context into the prompt, calls `chat()`. Used for providers without tool-use support (Ollama).

The use case selects the strategy based on provider capability. The strategy is injected into `ChatWithBookUseCase`.

**Rationale:** The strategy pattern cleanly separates the "how to retrieve" decision from the agent loop. Adding new strategies (e.g., a hybrid approach) requires no changes to the use case.

### 6. ConversationContextStrategy protocol

```python
class ConversationContextStrategy(Protocol):
    def build_context(
        self,
        history: list[ChatMessage],
    ) -> list[ChatMessage]:
        """Selects which messages to include in the LLM prompt."""
        ...
```

Single implementation for MVP:

- **`FullHistoryStrategy`**: Returns the last N messages (configurable, default determined during implementation). Includes `tool_result` messages in the history sent to the LLM so it can see prior retrieval results.

**Rationale:** The simplest strategy that enables multi-turn. The protocol makes it trivial to add sliding-window or summary-based strategies later.

### 7. ChatWithBookUseCase — the agent loop

This is the core orchestrator replacing `AskBookUseCase`.

```
Dependencies:
  - chat_provider: ChatProvider
  - retrieval_strategy: RetrievalStrategy
  - context_strategy: ConversationContextStrategy
  - search_use_case: SearchBooksUseCase
  - conversation_repo: ConversationRepository
  - message_repo: ChatMessageRepository
  - prompts_dir: Path

execute(conversation_id: str, user_message: str) -> str:
  1. Load conversation from conversation_repo (validates it exists)
  2. Load message history from message_repo
  3. Apply context_strategy to get the messages window
  4. Build system prompt from conversation_system_prompt.md template
  5. Construct PromptMessage list: system + context window + new user message
  6. Define the search_book tool (ToolDefinition)
  7. Define search_fn: a closure over search_use_case.execute(conversation.book_id, query)
  8. Call retrieval_strategy.execute(chat_provider, messages, tools, search_fn)
  9. Persist user message and all new messages (assistant, tool_result) via message_repo
  10. Return assistant response text
```

`AskBookUseCase` and `app/ask.py` are deleted entirely.

**Rationale:** The use case is a thin orchestrator. All intelligence about retrieval lives in the strategy. All intelligence about context selection lives in the context strategy. The use case just wires them together and handles persistence.

### 8. Repository protocols

Two new protocols in `domain/protocols.py`:

```python
class ConversationRepository(Protocol):
    def save(self, conversation: Conversation) -> None: ...
    def get(self, conversation_id: str) -> Conversation | None: ...
    def get_by_book(self, book_id: str) -> list[Conversation]: ...
    def delete(self, conversation_id: str) -> None: ...
    def update_title(self, conversation_id: str, title: str) -> None: ...

class ChatMessageRepository(Protocol):
    def save(self, message: ChatMessage) -> None: ...
    def save_batch(self, messages: list[ChatMessage]) -> None: ...
    def get_by_conversation(self, conversation_id: str) -> list[ChatMessage]: ...
    def delete_by_conversation(self, conversation_id: str) -> None: ...
```

SQLite adapters in `infra/storage/conversation_repo.py` and `infra/storage/chat_message_repo.py`.

### 9. Conversation management use case

A separate `ManageConversationsUseCase` (or a set of small use cases) in `app/conversations.py` handles:

- `create(book_id, title?) -> Conversation` — creates a new conversation for a book; auto-generates title if not provided
- `list_by_book(book_id) -> list[Conversation]` — lists all conversations for a book
- `rename(conversation_id, title)` — renames a conversation
- `delete(conversation_id)` — deletes a conversation and its messages

Auto-titling: the title is derived from the first user message (truncated to a reasonable length). This happens at creation time if no explicit title is provided. The use case can also update the title after the first message is sent if creation happens before the first message.

### 10. Prompt templates

Two new templates in `shared/prompts/`:

**`conversation_system_prompt.md`** — Replaces `system_prompt.md` for the agentic flow. Instructs the agent that it is a reading companion with access to a `search_book` tool. Includes rules:
- Answer only from retrieved passages or prior conversation context
- Use the `search_book` tool when you need information from the book
- Do not retrieve when the answer is already in the conversation context
- Reformulate search queries to be self-contained (resolve pronouns, references)
- Cite page numbers
- Do not reveal content beyond the reader's current position

**`reformulation_prompt.md`** — Used by `AlwaysRetrieveStrategy` to reformulate a user message into a self-contained search query using conversation context. Not used by the tool-use strategy (the LLM reformulates implicitly when composing tool arguments).

### 11. CLI chat command

Replace `cli ask` with `cli chat <book_id>`:

```
cli chat <book_id> [--conversation <id>] [--new] [--verbose]
```

Behavior:
1. If `--conversation <id>` is provided, resume that conversation
2. If `--new` is provided, create a new conversation
3. Otherwise, list existing conversations for the book and let the user select one, or create a new one
4. Enter a REPL loop: prompt for input, call `ChatWithBookUseCase.execute()`, print the response
5. With `--verbose`, print tool invocations and results between the user message and assistant response
6. Exit on `quit`, `exit`, or Ctrl+D

### 12. Error handling

Add `UNSUPPORTED_FEATURE` to `LLMErrorCode` for providers that do not support tool-use. The `AlwaysRetrieveStrategy` is the graceful degradation path — it does not require tool-use.

Add `ConversationError` (or extend `BookError`) for conversation-specific failures: `NOT_FOUND`, `INVALID_STATE`.

### 13. Delete cascade

Deleting a book must cascade to conversations and their messages. The SQL schema handles this via `ON DELETE CASCADE` on both `conversations.book_id` and `chat_messages.conversation_id`. The `DeleteBookUseCase` does not need changes — SQLite cascades handle it.

## Component diagram

```
CLI (chat command)
  │
  ▼
ChatWithBookUseCase
  ├── ConversationRepository     ── load/save conversation
  ├── ChatMessageRepository      ── load/save messages
  ├── ConversationContextStrategy ── select message window
  ├── RetrievalStrategy          ── agent loop (tool-use or always-retrieve)
  │     ├── ChatProvider.chat_with_tools()
  │     └── SearchBooksUseCase   ── vector search (existing)
  └── Prompt templates           ── system prompt, reformulation
```

## File changes summary

| Action | Path | Description |
|--------|------|-------------|
| Create | `domain/conversation.py` | `Conversation` entity |
| Modify | `domain/chat.py` | `ChatMessage`: replace `book_id` with `conversation_id`, add `TOOL_RESULT` to `MessageRole` |
| Modify | `domain/prompt_message.py` | Add optional `tool_use_id` and `tool_invocations` fields |
| Create | `domain/tool.py` | `ToolDefinition`, `ToolInvocation`, `ChatResponse` value objects |
| Modify | `domain/protocols.py` | Add `chat_with_tools()` to `ChatProvider`, add `RetrievalStrategy`, `ConversationContextStrategy`, `ConversationRepository`, `ChatMessageRepository` |
| Modify | `domain/errors.py` | Add `UNSUPPORTED_FEATURE` to `LLMErrorCode` |
| Create | `app/chat.py` | `ChatWithBookUseCase` |
| Create | `app/conversations.py` | Conversation management use cases |
| Delete | `app/ask.py` | Replaced by `app/chat.py` |
| Modify | `infra/llm/anthropic.py` | Implement `chat_with_tools()` |
| Create | `infra/retrieval/tool_use.py` | `ToolUseRetrievalStrategy` |
| Create | `infra/retrieval/always_retrieve.py` | `AlwaysRetrieveStrategy` |
| Create | `infra/context/full_history.py` | `FullHistoryStrategy` |
| Create | `infra/storage/conversation_repo.py` | SQLite `ConversationRepository` adapter |
| Create | `infra/storage/chat_message_repo.py` | SQLite `ChatMessageRepository` adapter |
| Modify | `main.py` | Remove `ask` command, add `chat` command with REPL |
| Modify | `shared/schema/001_initial.sql` | Add `conversations` table, rewrite `chat_messages` |
| Create | `shared/prompts/conversation_system_prompt.md` | Agentic system prompt |
| Create | `shared/prompts/reformulation_prompt.md` | Query reformulation instructions |

## Risks / Trade-offs

**Tool-use loop may not terminate.** The agent could invoke the search tool repeatedly without producing a final text response. Mitigation: cap the loop at a maximum number of iterations (e.g., 3). If exceeded, return an error or the last partial response.

**Full history may exceed context window.** For long conversations, sending all messages (even capped at N) could approach the model's context limit, especially with tool_result messages that contain chunk text. Mitigation: the cap N should be conservative (e.g., 20 messages). Future: switch to a summarization-based strategy.

**Tool result messages inflate history.** Each retrieval turn adds a tool_result message containing multiple chunks of text. These are persisted and re-sent on subsequent turns. Mitigation: the context strategy can filter or truncate tool_result content in older messages. This is a future optimization; for MVP, the cap N provides sufficient protection.

**Breaking schema change.** Rewriting `001_initial.sql` is safe only because `chat_messages` is unused. If any user has data in this table, it would be lost. Mitigation: this is pre-release software with no users. The risk is zero.

**Anthropic-only tool-use for MVP.** OpenAI's tool-use API has a different format. The OpenAI adapter (when added) will need its own `chat_with_tools()` mapping. The protocol abstraction makes this straightforward but it is not included in this change.

**AlwaysRetrieveStrategy quality.** The fallback strategy always retrieves, which means it may include irrelevant context when retrieval is unnecessary. This is an acceptable trade-off for providers without tool-use support. The reformulation prompt mitigates some of this by producing better search queries.
