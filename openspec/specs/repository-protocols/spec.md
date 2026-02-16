# repository-protocols

Storage protocol definitions in the domain layer. Located in `python/source/interactive_books/domain/protocols.py`.

## Requirements

### RP-1: BookRepository protocol

`BookRepository` protocol (using `typing.Protocol`) with methods:

- `save(book: Book) -> None` — insert or update a book
- `get(book_id: str) -> Book | None` — load a book by ID, returns None if not found
- `get_all() -> list[Book]` — list all books
- `delete(book_id: str) -> None` — delete a book (cascades handled by storage layer)

### RP-2: ChunkRepository protocol

`ChunkRepository` protocol (using `typing.Protocol`) with methods:

- `save_chunks(book_id: str, chunks: list[Chunk]) -> None` — bulk insert chunks for a book
- `get_by_book(book_id: str) -> list[Chunk]` — all chunks for a book, ordered by chunk_index
- `get_up_to_page(book_id: str, page: int) -> list[Chunk]` — chunks where start_page <= page, ordered by chunk_index
- `delete_by_book(book_id: str) -> None` — delete all chunks for a book

### RP-3: Domain layer isolation

`protocols.py` imports only from domain modules (Book, Chunk, ChatMessage) and the standard library. No imports from `infra/`, `app/`, or third-party packages.

### RP-4: Domain types only

All protocol method signatures use domain types (Book, Chunk, SearchResult, EmbeddingVector, etc.), not raw dicts, tuples, or database-specific types. The `EmbeddingRepository.search` method returns `list[tuple[str, float]]` as a lightweight return type for chunk_id + distance pairs.

### RP-5: Protocols enable testing

All protocols use `typing.Protocol` (structural subtyping) so test doubles can implement them without inheritance.
