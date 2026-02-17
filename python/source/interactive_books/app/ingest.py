from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    BookParser,
    BookRepository,
    ChunkRepository,
    TextChunker,
)

if TYPE_CHECKING:
    from interactive_books.app.embed import EmbedBookUseCase

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".epub", ".docx"}


class IngestBookUseCase:
    def __init__(
        self,
        *,
        pdf_parser: BookParser,
        txt_parser: BookParser,
        epub_parser: BookParser,
        docx_parser: BookParser,
        chunker: TextChunker,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        embed_use_case: EmbedBookUseCase | None = None,
    ) -> None:
        self._parsers: dict[str, BookParser] = {
            ".pdf": pdf_parser,
            ".txt": txt_parser,
            ".epub": epub_parser,
            ".docx": docx_parser,
        }
        self._chunker = chunker
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo
        self._embed_use_case = embed_use_case

    def execute(self, file_path: Path, title: str) -> tuple[Book, Exception | None]:
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
            parser = self._parsers[extension]
            pages = parser.parse(file_path)
            chunk_data_list = self._chunker.chunk(pages)

            chunks = [
                Chunk(
                    id=str(uuid.uuid4()),
                    book_id=book.id,
                    content=chunk_data.content,
                    start_page=chunk_data.start_page,
                    end_page=chunk_data.end_page,
                    chunk_index=chunk_data.chunk_index,
                )
                for chunk_data in chunk_data_list
            ]

            self._chunk_repo.save_chunks(book.id, chunks)
            book.complete_ingestion()
        except Exception:
            book.fail_ingestion()
            self._book_repo.save(book)
            raise

        self._book_repo.save(book)

        embed_error = self._auto_embed(book)
        return book, embed_error

    def _auto_embed(self, book: Book) -> Exception | None:
        if self._embed_use_case is None:
            return None
        try:
            self._embed_use_case.execute(book.id)
        except Exception as exc:
            return exc
        return None
