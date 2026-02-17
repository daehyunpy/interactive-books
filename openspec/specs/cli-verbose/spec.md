# cli-verbose

Verbose output contract across all CLI commands. Defines what each command logs when `--verbose` is set, including token counts, tool invocations, chunk boundaries, and embedding progress.

## Requirements

### Requirement: Ingest command verbose output

When `--verbose` is set, the `ingest` command SHALL print:

- Chunk count after ingestion: `[verbose] Ingested N chunks`
- Embedding batch progress (if auto-embed is active): `[verbose] Embedding batch M/N (K chunks)`

#### Scenario: Verbose ingest with auto-embed

- **WHEN** `cli ingest book.pdf --verbose` is executed with `OPENAI_API_KEY` set
- **THEN** verbose lines are printed for chunking and embedding progress

#### Scenario: Verbose ingest without API key

- **WHEN** `cli ingest book.pdf --verbose` is executed without `OPENAI_API_KEY`
- **THEN** verbose lines are printed for chunking only (no embedding lines)

### Requirement: Search command verbose output

When `--verbose` is set, the `search` command SHALL print:

- Provider info before search: `[verbose] Provider: <name>, Dimension: <dim>`
- Elapsed time and result count after search: `[verbose] Search completed in X.XXs, N results`

#### Scenario: Verbose search

- **WHEN** `cli search <book> <query> --verbose` is executed
- **THEN** provider info and search timing are printed

### Requirement: Embed command verbose output

When `--verbose` is set, the `embed` command SHALL print:

- Chunk count before embedding: `[verbose] Embedding N chunks`
- Provider info: `[verbose] Provider: <name>, Dimension: <dim>`
- Batch progress: `[verbose] Embedding batch M/N (K chunks)`
- Rate-limit retry info: `[verbose] Rate limited, retrying in X.Xs (attempt N)`

#### Scenario: Verbose embed

- **WHEN** `cli embed <book> --verbose` is executed
- **THEN** chunk count, provider info, and batch progress are printed

### Requirement: Chat command verbose output via event callback

When `--verbose` is set, the `chat` command SHALL print:

- Chat model name at session start: `[verbose] Chat model: <model-name>`
- Tool invocations inline: `[verbose] Tool call: <tool_name>(<args>)`
- Tool result summaries: `[verbose]   → N results (pages X-Y, ...)`
- Token usage per turn: `[verbose] Tokens: X in / Y out`

When `--verbose` is not set, none of these lines are printed — only the assistant's final response.

#### Scenario: Verbose chat with tool invocation

- **WHEN** `cli chat <book> --verbose` is running and the LLM invokes `search_book`
- **THEN** the tool call, result summary, and token usage are printed before the assistant response

#### Scenario: Verbose chat without tool invocation

- **WHEN** `cli chat <book> --verbose` is running and the LLM responds directly
- **THEN** only the token usage is printed (no tool call lines)

#### Scenario: Non-verbose chat hides all debug output

- **WHEN** `cli chat <book>` is running (no `--verbose`)
- **THEN** only the assistant response is printed

### Requirement: Verbose prefix format

All verbose output lines SHALL use the `[verbose]` prefix for consistent formatting and grep-ability.

#### Scenario: Verbose prefix consistency

- **WHEN** any command is run with `--verbose`
- **THEN** all debug output lines start with `[verbose]`
