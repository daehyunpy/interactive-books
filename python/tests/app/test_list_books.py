from interactive_books.app.list_books import ListBooksUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk


class FakeBookRepository:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.books[book.id] = book

    def get(self, book_id: str) -> Book | None:
        return self.books.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self.books.values())

    def delete(self, book_id: str) -> None:
        self.books.pop(book_id, None)


class FakeChunkRepository:
    def __init__(self) -> None:
        self.chunks: dict[str, list[Chunk]] = {}

    def save_chunks(self, book_id: str, chunks: list[Chunk]) -> None:
        self.chunks[book_id] = chunks

    def get_by_book(self, book_id: str) -> list[Chunk]:
        return self.chunks.get(book_id, [])

    def get_up_to_page(self, book_id: str, page: int) -> list[Chunk]:
        return [c for c in self.get_by_book(book_id) if c.start_page <= page]

    def count_by_book(self, book_id: str) -> int:
        return len(self.chunks.get(book_id, []))

    def delete_by_book(self, book_id: str) -> None:
        self.chunks.pop(book_id, None)


class TestListBooksUseCase:
    def test_returns_summaries_with_chunk_counts(self) -> None:
        book_repo = FakeBookRepository()
        chunk_repo = FakeChunkRepository()

        book = Book(
            id="b1",
            title="My Book",
            status=BookStatus.READY,
            embedding_provider="openai",
            current_page=5,
        )
        book_repo.save(book)
        chunk_repo.save_chunks(
            "b1",
            [
                Chunk(
                    id="c1",
                    book_id="b1",
                    content="A",
                    start_page=1,
                    end_page=1,
                    chunk_index=0,
                ),
                Chunk(
                    id="c2",
                    book_id="b1",
                    content="B",
                    start_page=2,
                    end_page=2,
                    chunk_index=1,
                ),
            ],
        )

        use_case = ListBooksUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            chunk_repo=chunk_repo,  # type: ignore[arg-type]
        )
        result = use_case.execute()

        assert len(result) == 1
        summary = result[0]
        assert summary.id == "b1"
        assert summary.title == "My Book"
        assert summary.status == BookStatus.READY
        assert summary.chunk_count == 2
        assert summary.embedding_provider == "openai"
        assert summary.current_page == 5

    def test_returns_empty_list_when_no_books(self) -> None:
        book_repo = FakeBookRepository()
        chunk_repo = FakeChunkRepository()

        use_case = ListBooksUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            chunk_repo=chunk_repo,  # type: ignore[arg-type]
        )
        result = use_case.execute()

        assert result == []

    def test_multiple_books_with_different_chunk_counts(self) -> None:
        book_repo = FakeBookRepository()
        chunk_repo = FakeChunkRepository()

        book_repo.save(Book(id="b1", title="Book One", status=BookStatus.READY))
        book_repo.save(Book(id="b2", title="Book Two", status=BookStatus.PENDING))
        chunk_repo.save_chunks(
            "b1",
            [
                Chunk(
                    id="c1",
                    book_id="b1",
                    content="A",
                    start_page=1,
                    end_page=1,
                    chunk_index=0,
                ),
                Chunk(
                    id="c2",
                    book_id="b1",
                    content="B",
                    start_page=2,
                    end_page=2,
                    chunk_index=1,
                ),
                Chunk(
                    id="c3",
                    book_id="b1",
                    content="C",
                    start_page=3,
                    end_page=3,
                    chunk_index=2,
                ),
            ],
        )
        # b2 has no chunks

        use_case = ListBooksUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            chunk_repo=chunk_repo,  # type: ignore[arg-type]
        )
        result = use_case.execute()

        by_id = {s.id: s for s in result}
        assert len(by_id) == 2
        assert by_id["b1"].chunk_count == 3
        assert by_id["b2"].chunk_count == 0
