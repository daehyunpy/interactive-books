from pathlib import Path

import pymupdf
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort


class PyMuPdfParser(BookParserPort):
    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )
        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"Failed to open PDF: {e}",
            ) from e

        try:
            return [
                PageContent(page_number=i + 1, text=str(doc[i].get_text()))
                for i in range(len(doc))
            ]
        finally:
            doc.close()
