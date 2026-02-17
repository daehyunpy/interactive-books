# repository-protocols

Delta spec for repository protocol additions. Adds `ConversationRepository` and `ChatMessageRepository` to support conversation persistence.

## ADDED Requirements

### Requirement: ConversationRepository protocol

The domain layer SHALL define a `ConversationRepository` protocol in `domain/protocols.py` (using `typing.Protocol`) with methods:

- `save(conversation: Conversation) -> None` — insert or update a conversation
- `get(conversation_id: str) -> Conversation | None` — load a conversation by ID, returns None if not found
- `get_by_book(book_id: str) -> list[Conversation]` — list all conversations for a book, ordered by `created_at` descending (most recent first)
- `delete(conversation_id: str) -> None` — delete a conversation (messages cascade via SQL foreign key)

#### Scenario: Save and retrieve a conversation

- **WHEN** a `Conversation` is saved via `save()` and then retrieved via `get()`
- **THEN** the returned conversation has the same `id`, `book_id`, `title`, and `created_at`

#### Scenario: Get conversation not found

- **WHEN** `get()` is called with a non-existent ID
- **THEN** `None` is returned

#### Scenario: List conversations for a book

- **WHEN** `get_by_book()` is called for a book with 3 conversations
- **THEN** all 3 conversations are returned, ordered by `created_at` descending

#### Scenario: List conversations for a book with none

- **WHEN** `get_by_book()` is called for a book with no conversations
- **THEN** an empty list is returned

#### Scenario: Delete conversation cascades to messages

- **WHEN** `delete()` is called for a conversation that has messages
- **THEN** the conversation and all its messages are removed from storage

### Requirement: ChatMessageRepository protocol

The domain layer SHALL define a `ChatMessageRepository` protocol in `domain/protocols.py` (using `typing.Protocol`) with methods:

- `save(message: ChatMessage) -> None` — insert a chat message
- `get_by_conversation(conversation_id: str) -> list[ChatMessage]` — all messages for a conversation, ordered by `created_at` ascending (chronological order)
- `delete_by_conversation(conversation_id: str) -> None` — delete all messages for a conversation

#### Scenario: Save and retrieve messages

- **WHEN** multiple `ChatMessage`s are saved for a conversation and then retrieved via `get_by_conversation()`
- **THEN** all messages are returned in chronological order (`created_at` ascending)

#### Scenario: Get messages for empty conversation

- **WHEN** `get_by_conversation()` is called for a conversation with no messages
- **THEN** an empty list is returned

#### Scenario: Delete messages by conversation

- **WHEN** `delete_by_conversation()` is called for a conversation with messages
- **THEN** all messages for that conversation are removed

#### Scenario: Messages from other conversations are unaffected

- **WHEN** `delete_by_conversation()` is called for conversation A
- **THEN** messages belonging to conversation B are not affected

## MODIFIED Requirements

### Requirement: Domain layer isolation (MODIFIED RP-3)

`protocols.py` imports only from domain modules (`Book`, `Chunk`, `ChatMessage`, `Conversation`, `PromptMessage`, `ToolDefinition`, `ChatResponse`) and the standard library. No imports from `infra/`, `app/`, or third-party packages.

**Changes from original:** Added `Conversation`, `ToolDefinition`, and `ChatResponse` to the list of allowed domain imports.

#### Scenario: No external imports in protocols

- **WHEN** `protocols.py` is analyzed for imports
- **THEN** all imports resolve to `domain/` modules or the standard library

### Requirement: Domain types only (MODIFIED RP-4)

All protocol method signatures use domain types (`Book`, `Chunk`, `Conversation`, `ChatMessage`, `SearchResult`, `EmbeddingVector`, `PromptMessage`, `ToolDefinition`, `ChatResponse`, etc.), not raw dicts, tuples, or database-specific types. The `EmbeddingRepository.search` method returns `list[tuple[str, float]]` as a lightweight return type for chunk_id + distance pairs. The `ChatProvider.chat` method accepts `list[PromptMessage]` and returns `str`. The `ChatProvider.chat_with_tools` method accepts `list[PromptMessage]` and `list[ToolDefinition]` and returns `ChatResponse`.

**Changes from original:** Added `Conversation`, `ChatMessage`, `ToolDefinition`, `ChatResponse` to domain types. Added `chat_with_tools` signature reference.

#### Scenario: Repository methods use domain types

- **WHEN** `ConversationRepository` and `ChatMessageRepository` method signatures are inspected
- **THEN** all parameters and return types are domain types (`Conversation`, `ChatMessage`, `str`, `list`, `None`)

### Requirement: Protocols enable testing (MODIFIED RP-5)

All protocols use `typing.Protocol` (structural subtyping) so test doubles can implement them without inheritance. This includes the new `ConversationRepository` and `ChatMessageRepository` protocols.

**Changes from original:** Scope expanded to include new repository protocols.

#### Scenario: Test double for ConversationRepository

- **WHEN** a test class implements all methods of `ConversationRepository` with matching signatures
- **THEN** it satisfies the protocol without inheriting from it

#### Scenario: Test double for ChatMessageRepository

- **WHEN** a test class implements all methods of `ChatMessageRepository` with matching signatures
- **THEN** it satisfies the protocol without inheriting from it
