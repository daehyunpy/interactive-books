from pathlib import Path

from selectolax.parser import HTMLParser

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort
from interactive_books.infra.parsers._html_text import extract_block_text


class BookParser(BookParserPort):
    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )

        text = file_path.read_text(encoding="utf-8")
        tree = HTMLParser(text)
        body = tree.body

        if body is None:
            return [PageContent(page_number=1, text="")]

        extracted = extract_block_text(body)
        if not extracted.strip():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"HTML has no text content: {file_path}",
            )

        return [PageContent(page_number=1, text=extracted)]
