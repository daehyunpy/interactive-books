## ADDED Requirements

### Requirement: AskBookUseCase orchestrates question answering

The application layer SHALL provide an `AskBookUseCase` class in `app/ask.py` that accepts `ChatProvider`, `SearchBooksUseCase`, and `prompts_dir: Path` via constructor injection. It SHALL expose an `execute(book_id: str, question: str, top_k: int = 5) → str` method that returns the LLM's answer.

#### Scenario: Successful question answering

- **WHEN** `execute` is called with a valid book ID and question
- **THEN** relevant chunks are retrieved, a prompt is assembled with context and citation instructions, the LLM is called, and the answer text is returned

#### Scenario: Book not found

- **WHEN** `execute` is called with a non-existent book ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

#### Scenario: Book has no embeddings

- **WHEN** `execute` is called for a book without embeddings
- **THEN** a `BookError` with code `INVALID_STATE` is raised

#### Scenario: No relevant chunks found

- **WHEN** the search returns zero results
- **THEN** the LLM is still called but the context indicates no relevant passages were found

#### Scenario: LLM call fails

- **WHEN** the ChatProvider raises an LLMError
- **THEN** the error propagates to the caller

### Requirement: Prompt assembly uses shared templates

The `AskBookUseCase` SHALL load prompt templates from `prompts_dir` and assemble the message list as:

1. System message: system prompt + citation instructions
2. User message: query template with `{context}` filled from search results and `{question}` filled from the user's question

#### Scenario: Context formatted with page labels

- **WHEN** search results are assembled into the context string
- **THEN** each passage is prefixed with its page range, e.g., "[Pages 42-43]:\n<content>"

#### Scenario: Multiple results joined

- **WHEN** multiple search results are available
- **THEN** they are joined with double newlines in the context string

### Requirement: CLI ask command wires the Q&A pipeline

The CLI SHALL provide an `ask` command that accepts a book ID and question string. It SHALL print the LLM's answer. It SHALL support a `--top-k` option (default 5) for controlling how many chunks are retrieved.

#### Scenario: Ask via CLI

- **WHEN** `cli ask <book-id> "What is this about?"` is executed
- **THEN** the answer is printed to stdout

#### Scenario: Ask with custom top-k

- **WHEN** `cli ask <book-id> <question> --top-k 10` is executed
- **THEN** up to 10 chunks are used as context for the answer

#### Scenario: Ask with invalid book ID

- **WHEN** `cli ask <invalid-id> <question>` is executed
- **THEN** an error message is displayed

#### Scenario: Ask when API key missing

- **WHEN** `ANTHROPIC_API_KEY` is not set
- **THEN** an error message is displayed indicating the key is required
