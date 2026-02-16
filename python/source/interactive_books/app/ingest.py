import uuid
from pathlib import Path

from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    BookParser,
    BookRepository,
    ChunkRepository,
    TextChunker,
)

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


class IngestBookUseCase:
    def __init__(
        self,
        *,
        pdf_parser: BookParser,
        txt_parser: BookParser,
        chunker: TextChunker,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
    ) -> None:
        self._pdf_parser = pdf_parser
        self._txt_parser = txt_parser
        self._chunker = chunker
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo

    def execute(self, file_path: Path, title: str) -> Book:
        extension = file_path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise BookError(
                BookErrorCode.UNSUPPORTED_FORMAT,
                f"Unsupported file format: {extension}",
            )

        book = Book(id=str(uuid.uuid4()), title=title)
        book.start_ingestion()
        self._book_repo.save(book)

        try:
            parser = self._pdf_parser if extension == ".pdf" else self._txt_parser
            pages = parser.parse(file_path)
            chunk_data_list = self._chunker.chunk(pages)

            chunks = [
                Chunk(
                    id=str(uuid.uuid4()),
                    book_id=book.id,
                    content=cd.content,
                    start_page=cd.start_page,
                    end_page=cd.end_page,
                    chunk_index=cd.chunk_index,
                )
                for cd in chunk_data_list
            ]

            self._chunk_repo.save_chunks(book.id, chunks)
            book.complete_ingestion()
        except Exception:
            book.fail_ingestion()
            self._book_repo.save(book)
            raise

        self._book_repo.save(book)
        return book
