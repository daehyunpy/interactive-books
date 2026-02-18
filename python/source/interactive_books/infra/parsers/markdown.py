from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort

HEADING_TAGS = frozenset({"h1", "h2"})


class BookParser(BookParserPort):
    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )

        text = file_path.read_text(encoding="utf-8")
        if not text.strip():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File is empty: {file_path}",
            )

        md = MarkdownIt()
        tokens = md.parse(text)
        sections = _split_by_headings(tokens)

        return [
            PageContent(page_number=i + 1, text=section)
            for i, section in enumerate(sections)
        ]


def _split_by_headings(tokens: list[Token]) -> list[str]:
    sections: list[str] = []
    current_parts: list[str] = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.type == "heading_open" and token.tag in HEADING_TAGS:
            if current_parts:
                sections.append("\n".join(current_parts))
                current_parts = []
            # Next token is the heading inline content
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                current_parts.append(_extract_inline_text(tokens[i + 1]))
            i += 3  # heading_open, inline, heading_close
            continue

        if token.type == "inline":
            plain = _extract_inline_text(token)
            if plain:
                current_parts.append(plain)

        i += 1

    if current_parts:
        sections.append("\n".join(current_parts))

    if not sections:
        sections.append("")

    return sections


def _extract_inline_text(token: Token) -> str:
    if not token.children:
        return token.content

    parts: list[str] = []
    for child in token.children:
        if child.type in ("text", "code_inline", "softbreak"):
            content = "\n" if child.type == "softbreak" else child.content
            parts.append(content)
    return "".join(parts)
