from pathlib import Path
from typing import TYPE_CHECKING

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

if TYPE_CHECKING:
    from docx.document import Document as DocumentClass

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort

HEADING_STYLES = frozenset({"Heading 1", "Heading 2"})


class BookParser(BookParserPort):
    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )
        try:
            doc = Document(str(file_path))
        except (PackageNotFoundError, Exception) as e:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"Failed to open DOCX: {e}",
            ) from e

        sections = self._split_by_headings(doc)

        all_text = "".join(text for text in sections)
        if not all_text.strip():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"DOCX has no text content: {file_path}",
            )

        return [
            PageContent(page_number=i + 1, text=text)
            for i, text in enumerate(sections)
        ]

    def _split_by_headings(self, doc: "DocumentClass") -> list[str]:
        sections: list[str] = []
        current_parts: list[str] = []

        for element in doc.element.body:
            tag = element.tag.split("}")[-1]

            if tag == "p":
                paragraph = Paragraph(element, doc)
                if paragraph.style and paragraph.style.name in HEADING_STYLES:
                    if current_parts:
                        sections.append("\n".join(current_parts))
                        current_parts = []
                    current_parts.append(paragraph.text)
                else:
                    text = paragraph.text
                    if text:
                        current_parts.append(text)

            elif tag == "tbl":
                table = Table(element, doc)
                table_text = _extract_table_text(table)
                if table_text:
                    current_parts.append(table_text)

        if current_parts:
            sections.append("\n".join(current_parts))

        if not sections:
            sections.append("")

        return sections


def _extract_table_text(table: Table) -> str:
    rows: list[str] = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)
