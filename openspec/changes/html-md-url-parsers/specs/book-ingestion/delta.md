## MODIFIED Requirements

### Requirement: IngestBookUseCase orchestrates the ingestion pipeline
The `IngestBookUseCase` constructor SHALL additionally accept `html_parser: BookParser`, `md_parser: BookParser`, and `url_parser: UrlParser` parameters. The `self._parsers` dict SHALL include `.html` and `.md` entries. The `url_parser` SHALL be stored separately for URL source handling.

The `execute` method signature SHALL change from `execute(file_path: Path, title: str)` to `execute(source: Path | str, title: str)`. When `source` is a `str` starting with `http://` or `https://`, the method SHALL delegate to `self._url_parser.parse_url(source)`. Otherwise, it SHALL convert to `Path` and use the existing file-extension-based routing.

#### Scenario: HTML file selects HTML parser
- **WHEN** a file with `.html` extension is provided
- **THEN** the HTML parser is used for extraction and the book reaches READY status

#### Scenario: Markdown file selects Markdown parser
- **WHEN** a file with `.md` extension is provided
- **THEN** the Markdown parser is used for extraction and the book reaches READY status

#### Scenario: URL source uses URL parser
- **WHEN** a URL string starting with `https://` is provided as source
- **THEN** the URL parser's `parse_url` method is called with the URL

#### Scenario: URL fetch failure during ingestion
- **WHEN** the URL parser raises `BookError(FETCH_FAILED)`
- **THEN** the book is saved with status FAILED and the error is re-raised

### Requirement: File format determines parser selection
The parser selection dict SHALL include `.html` → HTML parser and `.md` → Markdown parser in addition to the existing mappings. Supported extensions: `.pdf`, `.txt`, `.epub`, `.docx`, `.html`, `.md`.

### Requirement: CLI ingest command wires the pipeline
The CLI `ingest` command argument SHALL change from `file_path: Path` to `source: str` to handle both file paths and URLs. It SHALL detect URLs by prefix (`http://` or `https://`). For file paths, title defaults to the filename stem. For URLs, title defaults to the last path segment. The command SHALL additionally construct and pass `HtmlBookParser`, `MdBookParser`, and `UrlParser` to `IngestBookUseCase`.
