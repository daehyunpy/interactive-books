import zipfile
from pathlib import Path
from xml.etree import ElementTree

from selectolax.parser import HTMLParser

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser as BookParserPort

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
CONTAINER_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
CONTAINER_PATH = "META-INF/container.xml"
ENCRYPTION_PATH = "META-INF/encryption.xml"


class BookParser(BookParserPort):
    def parse(self, file_path: Path) -> list[PageContent]:
        if not file_path.exists():
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"File not found: {file_path}",
            )
        try:
            epub = zipfile.ZipFile(file_path, "r")
        except (zipfile.BadZipFile, Exception) as e:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                f"Failed to open EPUB: {e}",
            ) from e

        try:
            return self._parse_epub(epub)
        finally:
            epub.close()

    def _parse_epub(self, epub: zipfile.ZipFile) -> list[PageContent]:
        self._check_drm(epub)
        opf_path = self._find_opf_path(epub)
        content_paths = self._read_spine(epub, opf_path)

        if not content_paths:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                "EPUB contains no content documents",
            )

        return [
            PageContent(
                page_number=i + 1,
                text=self._extract_text(epub, path),
            )
            for i, path in enumerate(content_paths)
        ]

    def _check_drm(self, epub: zipfile.ZipFile) -> None:
        if ENCRYPTION_PATH in epub.namelist():
            raise BookError(
                BookErrorCode.DRM_PROTECTED,
                "EPUB is DRM-protected",
            )

    def _find_opf_path(self, epub: zipfile.ZipFile) -> str:
        try:
            container_xml = epub.read(CONTAINER_PATH)
        except KeyError as e:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                "EPUB missing META-INF/container.xml",
            ) from e

        root = ElementTree.fromstring(container_xml)
        rootfile = root.find(
            f".//{{{CONTAINER_NAMESPACE}}}rootfile"
        )
        if rootfile is None:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                "EPUB container.xml missing rootfile element",
            )

        opf_path = rootfile.get("full-path")
        if not opf_path:
            raise BookError(
                BookErrorCode.PARSE_FAILED,
                "EPUB rootfile missing full-path attribute",
            )
        return opf_path

    def _read_spine(self, epub: zipfile.ZipFile, opf_path: str) -> list[str]:
        opf_xml = epub.read(opf_path)
        root = ElementTree.fromstring(opf_xml)

        manifest_items: dict[str, str] = {}
        for item in root.findall(f".//{{{OPF_NAMESPACE}}}item"):
            item_id = item.get("id", "")
            href = item.get("href", "")
            if item_id and href:
                manifest_items[item_id] = href

        opf_dir = str(Path(opf_path).parent)
        content_paths: list[str] = []
        for itemref in root.findall(f".//{{{OPF_NAMESPACE}}}itemref"):
            idref = itemref.get("idref", "")
            href = manifest_items.get(idref)
            if href:
                if opf_dir and opf_dir != ".":
                    content_paths.append(f"{opf_dir}/{href}")
                else:
                    content_paths.append(href)

        return content_paths

    def _extract_text(self, epub: zipfile.ZipFile, path: str) -> str:
        xhtml = epub.read(path).decode("utf-8")
        tree = HTMLParser(xhtml)
        body = tree.body
        if body is None:
            return ""
        return _extract_block_text(body)


def _extract_block_text(node: object) -> str:
    """Extract text from an HTML node, preserving block-level line breaks."""
    BLOCK_TAGS = frozenset({
        "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "blockquote", "tr", "br", "section", "article",
    })
    parts: list[str] = []
    for child in node.iter():  # type: ignore[union-attr]
        if child.tag in BLOCK_TAGS and parts and parts[-1] != "\n":
            parts.append("\n")
        text = child.text(deep=False, strip=False) if hasattr(child, "text") else ""
        if text:
            parts.append(text)
    return "".join(parts).strip()
