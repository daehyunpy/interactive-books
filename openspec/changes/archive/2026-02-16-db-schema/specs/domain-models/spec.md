# domain-models

Domain entities and value objects enforcing cross-platform invariants. Located in `python/source/interactive_books/domain/`.

## Requirements

### DM-1: BookStatus enum

`BookStatus` enum with values: `PENDING`, `INGESTING`, `READY`, `FAILED`. String values are lowercase (`"pending"`, `"ingesting"`, `"ready"`, `"failed"`) for DB storage. Defined in `domain/book.py`.

### DM-2: Book aggregate root

`Book` dataclass with fields: `id` (str), `title` (str), `status` (BookStatus), `current_page` (int, default 0), `embedding_provider` (str | None, default None), `embedding_dimension` (int | None, default None), `created_at` (datetime), `updated_at` (datetime). Defined in `domain/book.py`.

### DM-3: Book title invariant

Book creation raises `BookError` if `title` is empty or whitespace-only. Enforced in `__post_init__`.

### DM-4: Book status transitions

Book provides named methods for status transitions:
- `start_ingestion()`: pending → ingesting
- `complete_ingestion()`: ingesting → ready
- `fail_ingestion()`: ingesting → failed
- `reset_to_pending()`: any → pending

Invalid transitions (e.g., pending → ready directly) raise `BookError`.

### DM-5: Book current page validation

`set_current_page(page: int)` accepts page >= 0. Page 0 means "no position set." Negative values raise `BookError`.

### DM-6: Book embedding provider switch

`switch_embedding_provider(provider: str, dimension: int)` updates `embedding_provider` and `embedding_dimension`, then calls `reset_to_pending()` — switching provider requires re-indexing.

### DM-7: Chunk value object

`Chunk` frozen dataclass with fields: `id` (str), `book_id` (str), `content` (str), `start_page` (int), `end_page` (int), `chunk_index` (int), `created_at` (datetime). Immutable after creation. Defined in `domain/chunk.py`.

### DM-8: Chunk page range invariant

Chunk creation raises `BookError` if `start_page < 1` or `end_page < start_page`. Enforced in `__post_init__`.

### DM-9: MessageRole enum

`MessageRole` enum with values: `USER`, `ASSISTANT`. String values are lowercase (`"user"`, `"assistant"`). Defined in `domain/chat.py`.

### DM-10: ChatMessage entity

`ChatMessage` frozen dataclass with fields: `id` (str), `book_id` (str), `role` (MessageRole), `content` (str), `created_at` (datetime). Defined in `domain/chat.py`.

### DM-11: No external dependencies

All domain model files import only from the standard library and other domain modules. No imports from `infra/`, `app/`, or third-party packages.
