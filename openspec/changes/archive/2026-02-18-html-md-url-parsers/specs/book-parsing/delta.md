## ADDED Requirements

### Requirement: HTML parser extracts text as a single page
The system SHALL provide an HTML parser adapter that implements `BookParser`. It SHALL use `selectolax` to parse the HTML file, extract text from the `<body>` element via `extract_block_text`, and return a single `PageContent` with `page_number=1`. If the body text is empty after stripping, it SHALL raise `BookError(PARSE_FAILED)`.

#### Scenario: Parse a well-formed HTML file
- **WHEN** an HTML file with paragraphs and headings is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1` and all text content extracted

#### Scenario: HTML with empty body
- **WHEN** an HTML file with an empty `<body>` element is parsed
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: File not found
- **WHEN** a non-existent HTML file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: Markdown parser extracts text with heading-based page boundaries
The system SHALL provide a Markdown parser adapter that implements `BookParser`. It SHALL use `markdown-it-py` to parse the file into a token stream, split at H1 (`#`) and H2 (`##`) headings, and extract plain text by walking inline children (stripping formatting markers). Content before the first heading SHALL be page 1. If no headings exist, the entire document SHALL be one page. If all text is empty, it SHALL raise `BookError(PARSE_FAILED)`.

#### Scenario: Parse Markdown with H1 and H2 headings
- **WHEN** a Markdown file with intro, H1, H2, and another H1 is parsed
- **THEN** the result contains 4 `PageContent` objects with sequential page numbers

#### Scenario: Parse Markdown with no headings
- **WHEN** a Markdown file with only paragraphs is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1`

#### Scenario: Headings inside code blocks are not page boundaries
- **WHEN** a Markdown file has `#` lines inside a fenced code block
- **THEN** those lines do not create page boundaries

#### Scenario: Formatting stripped to plain text
- **WHEN** a Markdown file with bold, italic, links, and inline code is parsed
- **THEN** the extracted text contains the content without formatting markers

#### Scenario: Empty Markdown file
- **WHEN** an empty Markdown file is parsed
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: File not found
- **WHEN** a non-existent Markdown file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: UrlParser protocol defines URL parsing contract
The domain layer SHALL define a `UrlParser` protocol with a method `parse_url(url: str) → list[PageContent]`. This is separate from `BookParser` because URLs require network I/O and Content-Type detection.

### Requirement: URL parser fetches and extracts text as a single page
The system SHALL provide a `UrlParser` adapter in `infra/parsers/url.py`. It SHALL fetch the URL with `httpx` (timeout 30s, follow redirects), validate the Content-Type, extract text, and return `list[PageContent]`. Content-Type routing: `text/html` → selectolax extraction, `text/plain` → raw text, `text/markdown` → markdown-it-py heading-based pages. Missing Content-Type SHALL be treated as HTML. Unsupported Content-Type SHALL raise `BookError(FETCH_FAILED)`.

#### Scenario: Fetch an HTML URL
- **WHEN** a URL returning `text/html` content is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1` and HTML tags stripped

#### Scenario: Fetch a plain text URL
- **WHEN** a URL returning `text/plain` content is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1` and raw text preserved

#### Scenario: Fetch a Markdown URL
- **WHEN** a URL returning `text/markdown` content is parsed
- **THEN** the result contains heading-based `PageContent` pages (same as file-based Markdown parsing)

#### Scenario: Network error
- **WHEN** a URL cannot be reached (connection error, timeout)
- **THEN** a `BookError` with code `FETCH_FAILED` is raised

#### Scenario: Non-2xx HTTP response
- **WHEN** the server returns a 404 or 500 status
- **THEN** a `BookError` with code `FETCH_FAILED` is raised

#### Scenario: Unsupported Content-Type
- **WHEN** the server returns `application/pdf` or another non-text type
- **THEN** a `BookError` with code `FETCH_FAILED` is raised with a message naming the unsupported type

#### Scenario: Empty content
- **WHEN** the fetched content has no extractable text
- **THEN** a `BookError` with code `FETCH_FAILED` is raised

### Requirement: FETCH_FAILED error code for URL-specific failures
The domain error taxonomy SHALL include `FETCH_FAILED = "fetch_failed"` in `BookErrorCode` for URL-specific errors (network, HTTP status, Content-Type, empty content).

## MODIFIED Requirements

### Requirement: Unsupported file formats are rejected
The system SHALL reject files with extensions other than `.pdf`, `.txt`, `.epub`, `.docx`, `.html`, and `.md` with a `BookError` using code `UNSUPPORTED_FORMAT`.

### Requirement: Shared text extraction for HTML content
The EPUB and HTML parsers SHALL share a common `extract_block_text` function in `infra/parsers/_html_text.py` for selectolax-based text extraction with block tag boundary handling.
