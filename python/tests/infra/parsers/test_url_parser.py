import httpx
import pytest

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.parsers.url import UrlParser


def _mock_transport(
    status_code: int = 200,
    content: bytes = b"",
    content_type: str = "text/html",
    headers: dict[str, str] | None = None,
) -> httpx.MockTransport:
    """Create a mock transport that returns a fixed response."""
    all_headers = {"content-type": content_type}
    if headers is not None:
        all_headers.update(headers)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            content=content,
            headers=all_headers,
        )

    return httpx.MockTransport(handler)


def _no_content_type_transport(content: bytes) -> httpx.MockTransport:
    """Create a transport that returns no Content-Type header."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, content=content)

    return httpx.MockTransport(handler)


def _error_transport() -> httpx.MockTransport:
    """Create a transport that raises a connection error."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    return httpx.MockTransport(handler)


class TestUrlParserHtml:
    def test_parse_url_returns_single_page(self) -> None:
        transport = _mock_transport(
            content=b"<html><body><p>Hello world.</p></body></html>",
            content_type="text/html",
        )
        parser = UrlParser(transport=transport)
        pages = parser.parse_url("https://example.com")
        assert len(pages) == 1
        assert pages[0].page_number == 1

    def test_parse_url_extracts_text(self) -> None:
        transport = _mock_transport(
            content=b"<html><body><p>First.</p><p>Second.</p></body></html>",
            content_type="text/html",
        )
        parser = UrlParser(transport=transport)
        pages = parser.parse_url("https://example.com")
        assert "First." in pages[0].text
        assert "Second." in pages[0].text
        assert "<p>" not in pages[0].text


class TestUrlParserPlainText:
    def test_parse_url_plain_text_content(self) -> None:
        transport = _mock_transport(
            content=b"This is plain text content.",
            content_type="text/plain",
        )
        parser = UrlParser(transport=transport)
        pages = parser.parse_url("https://example.com/file.txt")
        assert len(pages) == 1
        assert pages[0].text == "This is plain text content."


class TestUrlParserMarkdown:
    def test_parse_url_markdown_content_type_splits_by_heading(self) -> None:
        transport = _mock_transport(
            content=b"# Chapter One\n\nContent one.\n\n# Chapter Two\n\nContent two.\n",
            content_type="text/markdown",
        )
        parser = UrlParser(transport=transport)
        pages = parser.parse_url("https://example.com/readme.md")
        assert len(pages) == 2
        assert "Chapter One" in pages[0].text
        assert "Chapter Two" in pages[1].text


class TestUrlParserContentType:
    def test_parse_url_missing_content_type_treated_as_html(self) -> None:
        transport = _no_content_type_transport(
            content=b"<html><body><p>Fallback content.</p></body></html>",
        )
        parser = UrlParser(transport=transport)
        pages = parser.parse_url("https://example.com")
        assert "Fallback content." in pages[0].text

    def test_parse_url_unsupported_content_type_raises_fetch_failed(self) -> None:
        transport = _mock_transport(
            content=b"%PDF-1.4",
            content_type="application/pdf",
        )
        parser = UrlParser(transport=transport)
        with pytest.raises(BookError) as exc_info:
            parser.parse_url("https://example.com/doc.pdf")
        assert exc_info.value.code == BookErrorCode.FETCH_FAILED
        assert "application/pdf" in exc_info.value.message


class TestUrlParserErrors:
    def test_parse_url_network_error_raises_fetch_failed(self) -> None:
        transport = _error_transport()
        parser = UrlParser(transport=transport)
        with pytest.raises(BookError) as exc_info:
            parser.parse_url("https://example.com")
        assert exc_info.value.code == BookErrorCode.FETCH_FAILED

    def test_parse_url_non_2xx_raises_fetch_failed(self) -> None:
        transport = _mock_transport(
            status_code=404,
            content=b"Not Found",
            content_type="text/html",
        )
        parser = UrlParser(transport=transport)
        with pytest.raises(BookError) as exc_info:
            parser.parse_url("https://example.com/missing")
        assert exc_info.value.code == BookErrorCode.FETCH_FAILED

    def test_parse_url_empty_content_raises_fetch_failed(self) -> None:
        transport = _mock_transport(
            content=b"<html><body></body></html>",
            content_type="text/html",
        )
        parser = UrlParser(transport=transport)
        with pytest.raises(BookError) as exc_info:
            parser.parse_url("https://example.com/empty")
        assert exc_info.value.code == BookErrorCode.FETCH_FAILED
