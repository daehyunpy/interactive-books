## ADDED Requirements

### Requirement: BookSummary value object for book listings

The domain layer SHALL define a `BookSummary` frozen dataclass in `domain/book_summary.py` with fields: `id: str`, `title: str`, `status: BookStatus`, `chunk_count: int`, `embedding_provider: str | None`, `current_page: int`.

#### Scenario: BookSummary creation

- **WHEN** a `BookSummary` is created with valid fields
- **THEN** all fields are accessible and the object is immutable

### Requirement: ChunkRepository.count_by_book protocol and implementation

The `ChunkRepository` protocol SHALL add a `count_by_book(book_id: str) -> int` method. The `infra/storage/chunk_repo.py` implementation SHALL use `SELECT COUNT(*) FROM chunks WHERE book_id = ?`.

#### Scenario: Count chunks for a book with data

- **WHEN** `count_by_book` is called for a book with 5 chunks
- **THEN** 5 is returned

#### Scenario: Count chunks for a book with no chunks

- **WHEN** `count_by_book` is called for a book with no chunks
- **THEN** 0 is returned

### Requirement: ListBooksUseCase returns book summaries

The application layer SHALL provide a `ListBooksUseCase` class in `app/list_books.py` that accepts `BookRepository` and `ChunkRepository` via constructor injection. It SHALL use `chunk_repo.count_by_book(book_id)` to get chunk counts efficiently. It SHALL expose an `execute() → list[BookSummary]` method that returns all books with their chunk counts.

#### Scenario: List books with data

- **WHEN** `execute()` is called and books exist in the database
- **THEN** a list of `BookSummary` objects is returned, one per book, each with the correct chunk count

#### Scenario: List books when empty

- **WHEN** `execute()` is called and no books exist
- **THEN** an empty list is returned

### Requirement: DeleteBookUseCase removes a book and all associated data

The application layer SHALL provide a `DeleteBookUseCase` class in `app/delete_book.py` that accepts `BookRepository` and `EmbeddingRepository` via constructor injection. It SHALL expose an `execute(book_id: str) → Book` method that:

1. Fetches the book via `book_repo.get(book_id)` — raises `BookError(NOT_FOUND)` if missing
2. If `book.embedding_provider` and `book.embedding_dimension` are both non-None, calls `embedding_repo.delete_by_book(provider, dimension, book_id)` to clean up vec0 virtual table rows
3. Calls `book_repo.delete(book_id)` — chunks cascade automatically via SQL foreign key
4. Returns the deleted book

`ChunkRepository` is NOT needed — SQLite ON DELETE CASCADE handles chunk cleanup. Only vec0 virtual tables require explicit deletion because they don't participate in foreign key cascades.

#### Scenario: Successful deletion of book with embeddings

- **WHEN** `execute` is called with a valid book ID that has embeddings
- **THEN** embeddings are deleted from the vec0 table, the book and its chunks are deleted, and the deleted book is returned

#### Scenario: Successful deletion of book without embeddings

- **WHEN** `execute` is called with a valid book ID that was never embedded (embedding_provider is None)
- **THEN** the book and its chunks are deleted (no embedding cleanup needed), and the deleted book is returned

#### Scenario: Book not found

- **WHEN** `execute` is called with a non-existent book ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

### Requirement: CLI books command lists all books

The CLI SHALL provide a `books` command that prints a table of all books with columns: ID, title, status, chunks, embedding provider, and current page.

#### Scenario: Books listed

- **WHEN** `cli books` is executed and books exist
- **THEN** a formatted table of books is printed to stdout

#### Scenario: No books

- **WHEN** `cli books` is executed and no books exist
- **THEN** a message "No books found." is printed

### Requirement: CLI show command displays book details

The CLI SHALL provide a `show <book-id>` command that prints detailed information about a single book: ID, title, status, chunk count, embedding provider, embedding dimension, current page, created/updated timestamps.

#### Scenario: Show existing book

- **WHEN** `cli show <book-id>` is executed with a valid ID
- **THEN** detailed book information is printed

#### Scenario: Show non-existent book

- **WHEN** `cli show <book-id>` is executed with an invalid ID
- **THEN** an error message is displayed

### Requirement: CLI delete command removes a book

The CLI SHALL provide a `delete <book-id>` command that removes a book and all associated data. It SHALL prompt for confirmation by default and support a `--yes` / `-y` flag to skip confirmation.

#### Scenario: Delete with confirmation

- **WHEN** `cli delete <book-id>` is executed and user confirms
- **THEN** the book is deleted and a success message is printed

#### Scenario: Delete cancelled

- **WHEN** `cli delete <book-id>` is executed and user declines confirmation
- **THEN** the deletion is cancelled and a message is printed

#### Scenario: Delete with --yes flag

- **WHEN** `cli delete <book-id> --yes` is executed
- **THEN** the book is deleted without prompting for confirmation

#### Scenario: Delete non-existent book

- **WHEN** `cli delete <invalid-id>` is executed
- **THEN** an error message is displayed

### Requirement: CLI set-page command sets reading position

The CLI SHALL provide a `set-page <book-id> <page>` command that updates the book's current reading position. Page 0 means "no position set" (all pages eligible for search).

#### Scenario: Set page to valid value

- **WHEN** `cli set-page <book-id> 42` is executed
- **THEN** the book's current_page is updated to 42 and a confirmation message is printed

#### Scenario: Reset page to 0

- **WHEN** `cli set-page <book-id> 0` is executed
- **THEN** the book's current_page is reset to 0 and a confirmation message is printed

#### Scenario: Set page on non-existent book

- **WHEN** `cli set-page <invalid-id> 10` is executed
- **THEN** an error message is displayed
