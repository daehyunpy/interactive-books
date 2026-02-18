import httpx
from markdown_it import MarkdownIt
from selectolax.parser import HTMLParser

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import UrlParser as UrlParserPort
from interactive_books.infra.parsers._html_text import extract_block_text
from interactive_books.infra.parsers.markdown import _split_by_headings

FETCH_TIMEOUT = 30
SUPPORTED_CONTENT_TYPES = frozenset({"text/html", "text/plain", "text/markdown"})


class UrlParser(UrlParserPort):
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def parse_url(self, url: str) -> list[PageContent]:
        response = self._fetch(url)
        content_type = self._resolve_content_type(response)
        text = response.text

        if content_type == "text/plain":
            return self._parse_plain_text(text, url)
        if content_type == "text/markdown":
            return self._parse_markdown(text, url)
        return self._parse_html(text, url)

    def _fetch(self, url: str) -> httpx.Response:
        try:
            with httpx.Client(
                transport=self._transport,
                timeout=FETCH_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = client.get(url)
        except httpx.HTTPError as e:
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"Failed to fetch URL: {e}",
            ) from e

        if response.status_code >= 400:
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"HTTP {response.status_code} for URL: {url}",
            )

        return response

    def _resolve_content_type(self, response: httpx.Response) -> str:
        raw = response.headers.get("content-type", "")
        if not raw:
            return "text/html"
        media_type = raw.split(";")[0].strip().lower()

        if media_type not in SUPPORTED_CONTENT_TYPES:
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"Unsupported content type: {media_type}",
            )
        return media_type

    def _parse_html(self, text: str, url: str) -> list[PageContent]:
        tree = HTMLParser(text)
        body = tree.body
        if body is None:
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"No content found at URL: {url}",
            )

        extracted = extract_block_text(body)
        if not extracted.strip():
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"No text content at URL: {url}",
            )

        return [PageContent(page_number=1, text=extracted)]

    def _parse_plain_text(self, text: str, url: str) -> list[PageContent]:
        if not text.strip():
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"No text content at URL: {url}",
            )
        return [PageContent(page_number=1, text=text)]

    def _parse_markdown(self, text: str, url: str) -> list[PageContent]:
        if not text.strip():
            raise BookError(
                BookErrorCode.FETCH_FAILED,
                f"No text content at URL: {url}",
            )

        md = MarkdownIt()
        tokens = md.parse(text)
        sections = _split_by_headings(tokens)

        return [
            PageContent(page_number=i + 1, text=section)
            for i, section in enumerate(sections)
        ]
