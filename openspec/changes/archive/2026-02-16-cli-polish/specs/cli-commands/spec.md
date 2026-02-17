# cli-commands

Delta spec for CLI command polish: `ingest` auto-embeds, `embed` shows chunk count, conversation selection re-prompts on invalid input.

## MODIFIED Requirements

### CC-5: CLI ingest command wires the pipeline (MODIFIED)

The CLI `ingest` command SHALL accept a file path and optional `--title` (defaulting to filename stem). It SHALL construct `IngestBookUseCase` with parsers, chunker, and repositories. If `OPENAI_API_KEY` is available in the environment, it SHALL also construct `EmbedBookUseCase` and pass it as `embed_use_case` to `IngestBookUseCase` for auto-embedding.

After successful execution, the command SHALL print:
- Book ID, title, status, and chunk count
- If auto-embed succeeded: embedding provider and dimension
- If auto-embed was skipped (no API key): `Tip: set OPENAI_API_KEY and run 'embed <book-id>' to enable search.`
- If auto-embed failed: `Warning: embedding failed (<reason>). Run 'embed <book-id>' to retry.`

**Changes from original:**
- `ingest` now optionally auto-embeds after chunking when `OPENAI_API_KEY` is available
- Output includes embedding info or a hint to run `embed` manually
- `OPENAI_API_KEY` is NOT required — ingest still works without it (parse + chunk only)

#### Scenario: Ingest with auto-embed

- **WHEN** `cli ingest book.pdf` is executed with `OPENAI_API_KEY` set
- **THEN** the book is parsed, chunked, and embedded; output shows status, chunk count, and embedding info

#### Scenario: Ingest without API key

- **WHEN** `cli ingest book.pdf` is executed without `OPENAI_API_KEY`
- **THEN** the book is parsed and chunked but not embedded; output shows a tip about running `embed`

#### Scenario: Ingest with embed failure

- **WHEN** `cli ingest book.pdf` is executed and embedding fails (e.g., API error)
- **THEN** the book is still ingested (status READY); a warning is printed with the error reason

### CC-6: CLI embed command output includes chunk count (MODIFIED)

The CLI `embed` command output SHALL include the number of chunks embedded in its summary, in addition to the existing book ID, title, provider, and dimension fields.

**Changes from original:**
- Added `Chunks:` line to the embed output showing how many chunks were embedded

#### Scenario: Embed output shows chunk count

- **WHEN** `cli embed <book-id>` completes successfully
- **THEN** the output includes a line showing the number of chunks embedded (e.g., `Chunks:      47`)

### CC-9: CLI chat command replaces ask command (MODIFIED)

The `chat` command's conversation selection SHALL re-prompt on invalid input instead of silently creating a new conversation. When the user enters an invalid selection (non-numeric, out of range), the CLI SHALL print "Invalid choice, try again." and re-prompt. After 3 invalid attempts, a new conversation is created as fallback.

**Changes from original:**
- Invalid input now re-prompts (up to 3 times) instead of immediately creating a new conversation

#### Scenario: Re-prompt on invalid selection

- **WHEN** the user enters an invalid conversation selection (e.g., "abc" or "99")
- **THEN** "Invalid choice, try again." is printed and the prompt is shown again

#### Scenario: Fallback after max retries

- **WHEN** the user enters 3 consecutive invalid selections
- **THEN** a new conversation is created automatically
