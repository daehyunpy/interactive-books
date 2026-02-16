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

### Requirement: Unsupported file formats are rejected
The system SHALL reject files with extensions other than `.pdf` and `.txt` with a `BookError` using code `UNSUPPORTED_FORMAT`.

#### Scenario: Unsupported extension
- **WHEN** a file with extension `.docx` is provided for parsing
- **THEN** a `BookError` with code `UNSUPPORTED_FORMAT` is raised with a message naming the unsupported format
