# chat-cli

Interactive `cli chat <book>` command replacing `cli ask`, with conversation selection, multi-turn REPL, and `--verbose` event-based observability. Located in `python/source/interactive_books/main.py`.

## Requirements

### CCLI-1: CLI chat command starts an interactive conversation

The CLI SHALL provide a `chat <book-id>` command that starts an interactive conversation REPL about a book. The command SHALL validate that `OPENAI_API_KEY` (for embeddings/search) and `ANTHROPIC_API_KEY` (for chat) are set using the shared `_require_env` helper. Uses `_open_db` helper for database setup.

#### Scenario: Start chat with valid book

- **WHEN** `cli chat <book-id>` is executed with a valid book ID
- **THEN** the conversation selection interface is shown (per CCLI-2) and the REPL starts

#### Scenario: Chat with non-existent book

- **WHEN** `cli chat <invalid-id>` is executed
- **THEN** an error message is printed to stderr indicating the book was not found

#### Scenario: Missing API key

- **WHEN** `cli chat <book-id>` is executed without required API keys
- **THEN** an error message is printed indicating which key is missing

### CCLI-2: Conversation selection at chat start

When starting a chat, the CLI SHALL display existing conversations for the book and let the user choose:

1. If the book has existing conversations, list them (numbered, showing title and creation date) and offer "New conversation" as the first option
2. If the book has no conversations, automatically create a new conversation (the user's first message will be used as the auto-title)
3. The user selects by entering a number

#### Scenario: Book with existing conversations

- **WHEN** `cli chat <book-id>` is executed for a book with 3 conversations
- **THEN** a numbered list is shown: "1. New conversation", "2. <title1> (<date1>)", "3. <title2> (<date2>)", "4. <title3> (<date3>)"

#### Scenario: User selects existing conversation

- **WHEN** the user enters a number corresponding to an existing conversation
- **THEN** the REPL starts with that conversation's history loaded

#### Scenario: User creates new conversation

- **WHEN** the user selects "New conversation"
- **THEN** the REPL starts with an empty conversation (conversation is created after the first message is sent)

#### Scenario: Book with no conversations

- **WHEN** `cli chat <book-id>` is executed for a book with no conversations
- **THEN** a new conversation is started immediately without showing a selection menu

#### Scenario: Re-prompt on invalid selection

- **WHEN** the user enters an invalid conversation selection (e.g., "abc" or "99")
- **THEN** an invalid choice message is printed and the prompt is shown again

#### Scenario: Fallback after max retries

- **WHEN** the user enters 3 consecutive invalid selections
- **THEN** a new conversation is created automatically

### CCLI-3: Interactive REPL loop

The chat REPL SHALL:

1. Display a prompt (e.g., `You: `) and wait for user input
2. Send the user's message to `ChatWithBookUseCase.execute()`
3. Print the assistant's response (prefixed with e.g., `Assistant: `)
4. Repeat until the user exits
5. Handle empty input gracefully (skip, re-prompt)

#### Scenario: Multi-turn conversation

- **WHEN** the user sends multiple messages in sequence
- **THEN** each message is processed and the assistant response is printed, maintaining conversation context

#### Scenario: Empty input ignored

- **WHEN** the user presses Enter without typing anything
- **THEN** the prompt is shown again without sending a message

#### Scenario: LLM error during conversation

- **WHEN** the LLM API call fails during a conversation turn
- **THEN** an error message is printed to stderr and the REPL continues (does not crash)

### CCLI-4: REPL exit commands

The REPL SHALL exit gracefully when the user types `exit`, `quit`, or sends EOF (Ctrl+D). A farewell message SHALL be printed upon exit.

#### Scenario: Exit via command

- **WHEN** the user types `exit` or `quit`
- **THEN** the REPL exits with a farewell message

#### Scenario: Exit via EOF

- **WHEN** the user presses Ctrl+D (EOF)
- **THEN** the REPL exits with a farewell message

### CCLI-5: Verbose mode shows tool results via event callback

The `chat` command SHALL support `--verbose`. When enabled:

- Chat model name is displayed at the start of the session: `[verbose] Chat model: <name>`
- Tool invocations are printed inline: `[verbose] Tool call: <tool_name>(<args>)`
- Tool result summaries are printed: `[verbose]   → N results (pages X-Y, ...)`
- Token usage is printed per turn: `[verbose] Tokens: X in / Y out`

The CLI achieves this by passing an `on_event` callback to `ChatWithBookUseCase`. The callback receives `ChatEvent` objects and prints the appropriate `[verbose]` line for each event type.

When `--verbose` is not set, `on_event` is `None` and no debug output is printed.

#### Scenario: Verbose mode prints tool invocation details

- **WHEN** `cli chat <book-id> --verbose` is used and the LLM invokes `search_book` with query "protagonist motivations"
- **THEN** `[verbose] Tool call: search_book(query="protagonist motivations")` is printed

#### Scenario: Verbose mode prints tool result summary

- **WHEN** a tool invocation returns 3 results
- **THEN** `[verbose]   → 3 results (pages 12-14, 45-47, 89-91)` is printed

#### Scenario: Verbose mode prints token usage

- **WHEN** an LLM call completes with 1234 input tokens and 567 output tokens
- **THEN** `[verbose] Tokens: 1,234 in / 567 out` is printed

#### Scenario: Non-verbose hides all debug output

- **WHEN** `cli chat <book-id>` is used without `--verbose`
- **THEN** only the assistant response is printed; no `[verbose]` lines appear

### CCLI-6: New conversation is created on first message

When starting a new conversation (no existing conversation selected), the `Conversation` entity SHALL be created and persisted only when the user sends the first message. The first message's content is used for auto-titling.

#### Scenario: Conversation created on first message

- **WHEN** the user starts a new conversation and sends "Who is the protagonist?"
- **THEN** a `Conversation` is created with title "Who is the protagonist?" and the message is processed

#### Scenario: User exits before sending a message

- **WHEN** the user starts a new conversation but exits before sending any message
- **THEN** no conversation is created or persisted
