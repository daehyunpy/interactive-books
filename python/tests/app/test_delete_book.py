import pytest
from interactive_books.app.delete_book import DeleteBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.errors import BookError, BookErrorCode


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


class FakeEmbeddingRepository:
    def __init__(self) -> None:
        self.deleted: list[tuple[str, int, str]] = []

    def ensure_table(self, provider_name: str, dimension: int) -> None:
        pass

    def save_embeddings(
        self, provider_name: str, dimension: int, book_id: str, embeddings: list
    ) -> None:
        pass

    def delete_by_book(self, provider_name: str, dimension: int, book_id: str) -> None:
        self.deleted.append((provider_name, dimension, book_id))

    def has_embeddings(self, book_id: str, provider_name: str, dimension: int) -> bool:
        return False

    def search(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[str, float, int, int]]:
        return []


class TestDeleteBookUseCase:
    def test_deletes_book_with_embeddings(self) -> None:
        book_repo = FakeBookRepository()
        embedding_repo = FakeEmbeddingRepository()

        book = Book(
            id="b1",
            title="Test",
            status=BookStatus.READY,
            embedding_provider="openai",
            embedding_dimension=1536,
        )
        book_repo.save(book)

        use_case = DeleteBookUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            embedding_repo=embedding_repo,  # type: ignore[arg-type]
        )
        deleted = use_case.execute("b1")

        assert deleted.id == "b1"
        assert deleted.title == "Test"
        assert book_repo.get("b1") is None
        assert embedding_repo.deleted == [("openai", 1536, "b1")]

    def test_deletes_book_without_embeddings(self) -> None:
        book_repo = FakeBookRepository()
        embedding_repo = FakeEmbeddingRepository()

        book = Book(id="b1", title="No Embeddings", status=BookStatus.READY)
        book_repo.save(book)

        use_case = DeleteBookUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            embedding_repo=embedding_repo,  # type: ignore[arg-type]
        )
        deleted = use_case.execute("b1")

        assert deleted.id == "b1"
        assert book_repo.get("b1") is None
        assert embedding_repo.deleted == []

    def test_raises_not_found_for_missing_book(self) -> None:
        book_repo = FakeBookRepository()
        embedding_repo = FakeEmbeddingRepository()

        use_case = DeleteBookUseCase(
            book_repo=book_repo,  # type: ignore[arg-type]
            embedding_repo=embedding_repo,  # type: ignore[arg-type]
        )

        with pytest.raises(BookError) as exc_info:
            use_case.execute("nonexistent")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND
