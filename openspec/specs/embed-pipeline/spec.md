# embed-pipeline

Embedding orchestration use case and CLI command. Coordinates chunk embedding via the `EmbedBookUseCase` with batching, re-embed support, and failure cleanup.

## Requirements

### EPL-1: EmbedBookUseCase orchestrates chunk embedding

The application layer SHALL provide an `EmbedBookUseCase` class in `app/embed.py` that accepts `EmbeddingProvider`, `BookRepository`, `ChunkRepository`, and `EmbeddingRepository` via constructor injection. It SHALL expose an `execute(book_id: str) → Book` method.

#### Scenario: Successful embedding of a book's chunks
- **WHEN** `execute` is called with a valid book ID that has chunks
- **THEN** all chunks are embedded, vectors are stored in the per-provider table, `book.embedding_provider` and `book.embedding_dimension` are set, and the updated `Book` is returned

#### Scenario: Book not found
- **WHEN** `execute` is called with a non-existent book ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

#### Scenario: Book has no chunks
- **WHEN** `execute` is called for a book with zero chunks
- **THEN** a `BookError` with code `INVALID_STATE` is raised with a message indicating no chunks exist

### EPL-2: Chunks are embedded in batches

The use case SHALL embed chunks in batches of configurable size (default: 100). Each batch is a single call to `EmbeddingProvider.embed`.

#### Scenario: Book with fewer chunks than batch size
- **WHEN** a book has 50 chunks and batch size is 100
- **THEN** one batch call is made with all 50 chunk contents

#### Scenario: Book with more chunks than batch size
- **WHEN** a book has 250 chunks and batch size is 100
- **THEN** three batch calls are made (100, 100, 50)

### EPL-3: Existing embeddings are replaced on re-embed

The use case SHALL delete any existing embeddings for the book (via `delete_by_book`) before storing fresh embeddings.

#### Scenario: Re-embed a previously embedded book
- **WHEN** `execute` is called for a book that already has embeddings
- **THEN** the old embeddings are deleted from the per-provider table, and fresh embeddings are stored

### EPL-4: Embedding failure does not corrupt book state

If the embedding provider raises an error, the use case SHALL clean up any partially stored embeddings and leave the book's `embedding_provider` and `embedding_dimension` unchanged.

#### Scenario: API failure during embedding
- **WHEN** the embedding provider raises an error midway through embedding
- **THEN** any partially stored embeddings are cleaned up, the book's embedding metadata remains unchanged, and the error is re-raised

### EPL-5: CLI embed command wires the pipeline

The CLI SHALL provide an `embed` command that accepts a book ID. It SHALL print the book title, embedding provider, dimension, and vector count on success.

#### Scenario: Embed a book via CLI
- **WHEN** `cli embed <book-id>` is executed
- **THEN** the book's chunks are embedded and a summary is printed showing title, provider, dimension, and vector count

#### Scenario: Embed with invalid book ID
- **WHEN** `cli embed <invalid-id>` is executed
- **THEN** an error message is displayed indicating the book was not found
