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

### Requirement: Unsupported file formats are rejected
The system SHALL reject files with extensions other than `.pdf`, `.txt`, `.epub`, and `.docx` with a `BookError` using code `UNSUPPORTED_FORMAT`.

#### Scenario: Unsupported extension
- **WHEN** a file with extension `.xyz` is provided for parsing
- **THEN** a `BookError` with code `UNSUPPORTED_FORMAT` is raised with a message naming the unsupported format
