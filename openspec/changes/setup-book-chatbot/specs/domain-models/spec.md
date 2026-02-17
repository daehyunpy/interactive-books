# domain-models

Delta spec for domain model changes to support agentic conversation. Adds `Conversation` entity, modifies `ChatMessage` to use `conversation_id` instead of `book_id`, and extends `MessageRole` with `TOOL_RESULT`.

## ADDED Requirements

### DM-12: Conversation entity

The domain layer SHALL define a `Conversation` dataclass in `domain/conversation.py` with fields: `id` (str), `book_id` (str), `title` (str), `created_at` (datetime). `Conversation` is an aggregate root. See `conversation-management` spec for full behavioral requirements.

#### Scenario: Conversation creation

- **WHEN** a `Conversation` is created with valid fields
- **THEN** all fields are accessible

#### Scenario: Conversation in domain model graph

- **WHEN** the domain model is examined
- **THEN** `Conversation` sits between `Book` and `ChatMessage`: a `Book` has many `Conversation`s, each `Conversation` has many `ChatMessage`s

## MODIFIED Requirements

### DM-9: MessageRole enum (MODIFIED)

`MessageRole` enum with values: `USER`, `ASSISTANT`, `TOOL_RESULT`. String values are lowercase (`"user"`, `"assistant"`, `"tool_result"`). Defined in `domain/chat.py`.

The `TOOL_RESULT` value is added to support persisting tool invocation results in conversation history. Tool result messages contain the search results returned by the `search_book` tool and are included in conversation context sent to the LLM.

#### Scenario: MessageRole includes TOOL_RESULT

- **WHEN** `MessageRole` values are enumerated
- **THEN** `USER`, `ASSISTANT`, and `TOOL_RESULT` are all present

#### Scenario: TOOL_RESULT string value

- **WHEN** `MessageRole.TOOL_RESULT.value` is accessed
- **THEN** the value is `"tool_result"`

### DM-10: ChatMessage entity (MODIFIED)

`ChatMessage` frozen dataclass with fields: `id` (str), `conversation_id` (str), `role` (MessageRole), `content` (str), `created_at` (datetime). Defined in `domain/chat.py`.

**Changes from original:**
- `book_id` field is REMOVED
- `conversation_id` field is ADDED -- the message belongs to a `Conversation`, not directly to a `Book`
- The book is reachable via `message -> conversation -> book`

#### Scenario: ChatMessage with conversation_id

- **WHEN** a `ChatMessage` is created with a valid `conversation_id`
- **THEN** the `conversation_id` field is accessible and there is no `book_id` field

#### Scenario: ChatMessage with TOOL_RESULT role

- **WHEN** a `ChatMessage` is created with `role=MessageRole.TOOL_RESULT`
- **THEN** the message is valid and the content contains tool result data

#### Scenario: ChatMessage immutability

- **WHEN** an attempt is made to modify a `ChatMessage` field after creation
- **THEN** a `FrozenInstanceError` is raised

## REMOVED Requirements

### DM-10 (original): ChatMessage with book_id

**Reason:** `ChatMessage` no longer references `Book` directly. The `book_id` field is replaced by `conversation_id`. Messages are accessed through their parent `Conversation`, which holds the `book_id`.

**Migration:** Replace all `ChatMessage.book_id` references with `ChatMessage.conversation_id`. Access the book via `conversation.book_id` when needed.
