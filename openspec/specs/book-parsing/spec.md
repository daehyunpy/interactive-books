## ADDED Requirements

### Requirement: BookParser protocol defines file parsing contract
The domain layer SHALL define a `BookParser` protocol with a method `parse(file_path: Path) → list[PageContent]`. The protocol SHALL be defined in `domain/protocols.py` alongside existing protocols. Implementations SHALL NOT be imported by domain code.

#### Scenario: Protocol is defined in domain layer
- **WHEN** a developer imports from `domain/protocols.py`
- **THEN** `BookParser` is available as a Protocol class with a `parse` method

### Requirement: PageContent value object represents a single page of extracted text
The domain layer SHALL define a `PageContent` frozen dataclass with `page_number: int` and `text: str`. `page_number` MUST be >= 1. `text` MAY be empty (for pages that failed to parse).

#### Scenario: Valid PageContent creation
- **WHEN** `PageContent(page_number=1, text="Hello world")` is created
- **THEN** the object is created successfully with the given values

#### Scenario: Invalid page number rejected
- **WHEN** `PageContent(page_number=0, text="Hello")` is created
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: PDF parser extracts text with page boundaries
The system SHALL provide a `PyMuPdfParser` adapter that implements `BookParser`. It SHALL extract text from each page of a PDF file and return a `PageContent` per page with the correct `page_number` (1-indexed).

#### Scenario: Parse a multi-page PDF
- **WHEN** a PDF with 3 pages of text content is parsed
- **THEN** the result contains 3 `PageContent` objects with `page_number` 1, 2, and 3 and non-empty `text`

#### Scenario: Parse a PDF with an unparseable page
- **WHEN** a PDF has a page that produces no extractable text (e.g., a scanned image page)
- **THEN** that page's `PageContent` has empty `text` and the remaining pages are still returned

#### Scenario: File not found
- **WHEN** a non-existent file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: File is not a valid PDF
- **WHEN** a corrupted or non-PDF file is provided with a `.pdf` extension
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: Plain text parser extracts text with estimated page boundaries
The system SHALL provide a `PlainTextParser` adapter that implements `BookParser`. It SHALL divide the text into estimated pages using a configurable `chars_per_page` parameter (default: 3000).

#### Scenario: Parse a short text file
- **WHEN** a TXT file with 2500 characters is parsed with default `chars_per_page=3000`
- **THEN** the result contains 1 `PageContent` with `page_number=1`

#### Scenario: Parse a text file spanning multiple estimated pages
- **WHEN** a TXT file with 7000 characters is parsed with `chars_per_page=3000`
- **THEN** the result contains 3 `PageContent` objects with `page_number` 1, 2, and 3

#### Scenario: Empty text file
- **WHEN** an empty TXT file is parsed
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: File not found
- **WHEN** a non-existent file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: EPUB parser extracts text with chapter-based page boundaries
The system SHALL provide an EPUB parser adapter that implements `BookParser`. It SHALL read the EPUB ZIP archive, parse `META-INF/container.xml` to find the OPF path, parse the OPF manifest and spine for content document ordering, and use `selectolax` to strip XHTML tags from each content document. Each spine-ordered chapter SHALL produce one `PageContent` with 1-indexed page numbers.

#### Scenario: Parse a multi-chapter EPUB
- **WHEN** an EPUB with 3 chapters is parsed
- **THEN** the result contains 3 `PageContent` objects with `page_number` 1, 2, and 3

#### Scenario: Parse a single-chapter EPUB
- **WHEN** an EPUB with 1 chapter is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1`

#### Scenario: Chapter with only whitespace
- **WHEN** an EPUB has a chapter containing only whitespace
- **THEN** that chapter is included as a `PageContent` with empty/whitespace text

#### Scenario: DRM-protected EPUB rejected
- **WHEN** an EPUB containing `META-INF/encryption.xml` is parsed
- **THEN** a `BookError` with code `DRM_PROTECTED` is raised

#### Scenario: File not found
- **WHEN** a non-existent EPUB file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: Invalid EPUB file
- **WHEN** a corrupted or non-ZIP file with `.epub` extension is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: EPUB with no content documents
- **WHEN** an EPUB with an empty spine is parsed
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: DOCX parser extracts text with heading-based page boundaries
The system SHALL provide a DOCX parser adapter that implements `BookParser`. It SHALL use `python-docx` to iterate paragraphs and tables in document order, split at `Heading 1` and `Heading 2` paragraph styles. Content before the first heading SHALL be page 1. Each heading SHALL start a new page. Table cell text SHALL be extracted row by row. Images and embedded objects SHALL be ignored.

#### Scenario: Parse a multi-section DOCX with headings
- **WHEN** a DOCX with intro text, H1, content, H2, content, and another H1 is parsed
- **THEN** the result contains 4 `PageContent` objects (intro, first H1 section, H2 section, second H1 section)

#### Scenario: Parse a DOCX with no headings
- **WHEN** a DOCX with only paragraphs (no H1/H2 headings) is parsed
- **THEN** the result contains 1 `PageContent` with `page_number=1` containing all text

#### Scenario: DOCX with tables
- **WHEN** a DOCX containing tables is parsed
- **THEN** table cell text is included in the output

#### Scenario: Empty DOCX
- **WHEN** a DOCX with no text content is parsed
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: File not found
- **WHEN** a non-existent DOCX file path is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: Invalid DOCX file
- **WHEN** a corrupted or non-DOCX file with `.docx` extension is provided
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

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

### Requirement: Unsupported file formats are rejected
The system SHALL reject files with extensions other than `.pdf`, `.txt`, `.epub`, `.docx`, `.html`, and `.md` with a `BookError` using code `UNSUPPORTED_FORMAT`.

#### Scenario: Unsupported extension
- **WHEN** a file with extension `.xyz` is provided for parsing
- **THEN** a `BookError` with code `UNSUPPORTED_FORMAT` is raised with a message naming the unsupported format

### Requirement: Shared text extraction for HTML content
The EPUB and HTML parsers SHALL share a common `extract_block_text` function in `infra/parsers/_html_text.py` for selectolax-based text extraction with block tag boundary handling.
