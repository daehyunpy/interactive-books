import math
from pathlib import Path

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort

DEFAULT_CHARS_PER_PAGE = 3000


class PlainTextParser(BookParserPort):
    def __init__(self, chars_per_page: int = DEFAULT_CHARS_PER_PAGE) -> None:
        self._chars_per_page = chars_per_page

    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )

        text = file_path.read_text(encoding="utf-8")
        if not text:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File is empty: {file_path}",
            )

        total_pages = math.ceil(len(text) / self._chars_per_page)
        return [
            PageContent(
                page_number=i + 1,
                text=text[i * self._chars_per_page : (i + 1) * self._chars_per_page],
            )
            for i in range(total_pages)
        ]
