import math
from pathlib import Path

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent

DEFAULT_CHARS_PER_PAGE = 3000


class PlainTextParser:
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
        pages: list[PageContent] = []
        for i in range(total_pages):
            start = i * self._chars_per_page
            end = start + self._chars_per_page
            pages.append(PageContent(page_number=i + 1, text=text[start:end]))

        return pages
