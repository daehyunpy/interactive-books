# conversation-management

Conversation aggregate, repository implementation, CRUD operations, auto-titling, rename, and cascade deletion. Located in `python/source/interactive_books/domain/conversation.py`, `python/source/interactive_books/app/conversations.py`, and `python/source/interactive_books/infra/storage/conversation_repo.py`.

## ADDED Requirements

### CM-1: Conversation entity is an aggregate root

The domain layer SHALL define a `Conversation` dataclass in `domain/conversation.py` with fields: `id` (str), `book_id` (str), `title` (str), `created_at` (datetime). `Conversation` is an aggregate root alongside `Book`. A `Conversation` always belongs to exactly one `Book` (via `book_id`).

#### Scenario: Valid conversation creation

- **WHEN** a `Conversation` is created with a valid `id`, `book_id`, `title`, and `created_at`
- **THEN** all fields are accessible and the entity is fully initialized

#### Scenario: Conversation identity

- **WHEN** two `Conversation` instances have the same `id`
- **THEN** they represent the same aggregate regardless of other field values

### CM-2: Conversation title invariant

Conversation creation SHALL raise `BookError` if `title` is empty or whitespace-only. This invariant MUST be enforced in `__post_init__`.

#### Scenario: Empty title rejected

- **WHEN** a `Conversation` is created with `title=""`
- **THEN** a `BookError` is raised

#### Scenario: Whitespace-only title rejected

- **WHEN** a `Conversation` is created with `title="   "`
- **THEN** a `BookError` is raised

#### Scenario: Valid title accepted

- **WHEN** a `Conversation` is created with `title="Chapter 1 discussion"`
- **THEN** the conversation is created successfully

### CM-3: Conversation rename

The `Conversation` entity SHALL provide a `rename(new_title: str)` method that updates the `title` field. The method SHALL raise `BookError` if the new title is empty or whitespace-only.

#### Scenario: Rename with valid title

- **WHEN** `rename("New discussion title")` is called
- **THEN** the conversation's `title` is updated to `"New discussion title"`

#### Scenario: Rename with empty title rejected

- **WHEN** `rename("")` is called
- **THEN** a `BookError` is raised and the title remains unchanged

### CM-4: Conversation auto-titling from first user message

The application layer SHALL auto-generate a conversation title from the first user message. The title SHALL be truncated to a reasonable length (e.g., first 50 characters of the message, with "..." appended if truncated). The auto-title is applied at conversation creation time.

#### Scenario: Short first message becomes title

- **WHEN** a conversation is created with first message "Who is the main character?"
- **THEN** the conversation title is set to "Who is the main character?"

#### Scenario: Long first message is truncated

- **WHEN** a conversation is created with a first message longer than 50 characters
- **THEN** the conversation title is the first 50 characters followed by "..."

### CM-5: ConversationRepository SQLite implementation

The infrastructure layer SHALL provide a `ConversationRepository` adapter in `infra/storage/conversation_repo.py` that persists conversations to SQLite. It SHALL implement all methods defined in the `ConversationRepository` protocol (see repository-protocols spec).

#### Scenario: Save and retrieve a conversation

- **WHEN** a `Conversation` is saved via `save()` and then retrieved via `get()`
- **THEN** the returned conversation has identical field values

#### Scenario: List conversations by book

- **WHEN** `get_by_book(book_id)` is called for a book with 3 conversations
- **THEN** all 3 conversations are returned, ordered by `created_at` descending (newest first)

#### Scenario: List conversations for book with none

- **WHEN** `get_by_book(book_id)` is called for a book with no conversations
- **THEN** an empty list is returned

#### Scenario: Delete a conversation

- **WHEN** `delete(conversation_id)` is called for an existing conversation
- **THEN** the conversation is removed from storage

#### Scenario: Delete cascades from book

- **WHEN** a book is deleted from the `books` table
- **THEN** all conversations referencing that book are also deleted (via SQL ON DELETE CASCADE)

### CM-6: CreateConversationUseCase

The application layer SHALL provide a `CreateConversationUseCase` class in `app/conversations.py` that accepts `BookRepository` and `ConversationRepository` via constructor injection. It SHALL expose `execute(book_id: str, first_message: str) -> Conversation` that:

1. Validates the book exists via `book_repo.get(book_id)` -- raises `BookError(NOT_FOUND)` if missing
2. Generates a conversation ID (UUID)
3. Auto-generates a title from `first_message` (per CM-4)
4. Creates and saves the `Conversation`
5. Returns the created `Conversation`

#### Scenario: Create conversation for existing book

- **WHEN** `execute` is called with a valid book ID and first message
- **THEN** a new conversation is created, persisted, and returned with an auto-generated title

#### Scenario: Create conversation for non-existent book

- **WHEN** `execute` is called with a non-existent book ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

### CM-7: ListConversationsUseCase

The application layer SHALL provide a `ListConversationsUseCase` class in `app/conversations.py` that accepts `ConversationRepository` via constructor injection. It SHALL expose `execute(book_id: str) -> list[Conversation]` that returns all conversations for the given book, ordered by `created_at` descending.

#### Scenario: List conversations for book with data

- **WHEN** `execute` is called for a book with conversations
- **THEN** all conversations are returned ordered newest first

#### Scenario: List conversations for book with none

- **WHEN** `execute` is called for a book with no conversations
- **THEN** an empty list is returned

### CM-8: DeleteConversationUseCase

The application layer SHALL provide a `DeleteConversationUseCase` class in `app/conversations.py` that accepts `ConversationRepository` via constructor injection. It SHALL expose `execute(conversation_id: str) -> None` that deletes the conversation. Associated messages are cascade-deleted by the SQL foreign key constraint.

#### Scenario: Delete existing conversation

- **WHEN** `execute` is called with a valid conversation ID
- **THEN** the conversation and its messages are deleted

#### Scenario: Delete non-existent conversation

- **WHEN** `execute` is called with a non-existent conversation ID
- **THEN** the operation completes without error (idempotent)

### CM-9: RenameConversationUseCase

The application layer SHALL provide a `RenameConversationUseCase` class in `app/conversations.py` that accepts `ConversationRepository` via constructor injection. It SHALL expose `execute(conversation_id: str, new_title: str) -> Conversation` that:

1. Fetches the conversation via `conversation_repo.get(conversation_id)` -- raises `BookError(NOT_FOUND)` if missing
2. Calls `conversation.rename(new_title)` (validates non-empty)
3. Saves the updated conversation
4. Returns the updated conversation

#### Scenario: Rename existing conversation

- **WHEN** `execute` is called with a valid ID and non-empty title
- **THEN** the conversation title is updated, persisted, and the updated conversation is returned

#### Scenario: Rename non-existent conversation

- **WHEN** `execute` is called with a non-existent conversation ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

#### Scenario: Rename with empty title

- **WHEN** `execute` is called with an empty title
- **THEN** a `BookError` is raised

### CM-10: Cascade delete conversations when book is deleted

When a `Book` is deleted (via `DeleteBookUseCase` or SQL CASCADE), all `Conversation` entities belonging to that book SHALL be deleted. All `ChatMessage` entities belonging to those conversations SHALL also be deleted. This is enforced by SQL `ON DELETE CASCADE` foreign key constraints.

#### Scenario: Book deletion cascades to conversations and messages

- **WHEN** a book with 2 conversations (each with 5 messages) is deleted
- **THEN** both conversations and all 10 messages are deleted

### CM-11: No external dependencies in domain

The `Conversation` entity in `domain/conversation.py` SHALL import only from the standard library and other domain modules. No imports from `infra/`, `app/`, or third-party packages.

#### Scenario: Domain isolation

- **WHEN** `domain/conversation.py` is inspected
- **THEN** all imports are from the standard library or domain modules only
