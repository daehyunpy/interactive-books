# chat-agent

Agentic chat loop use case: `ChatWithBookUseCase`, tool-use integration, retrieval strategy, conversation context strategy, prompt assembly, event observability, and message persistence. Located in `python/source/interactive_books/app/chat.py` and `python/source/interactive_books/domain/protocols.py`.

## Requirements

### CA-1: ChatWithBookUseCase orchestrates agentic conversation

The application layer SHALL provide a `ChatWithBookUseCase` class in `app/chat.py` that accepts `ChatProvider`, `SearchBooksUseCase`, `ChatMessageRepository`, `ConversationRepository`, `BookRepository`, `RetrievalStrategy`, `ConversationContextStrategy`, `prompts_dir: Path`, and an optional `on_event: Callable[[ChatEvent], None] | None = None` via constructor injection. It SHALL expose `execute(conversation_id: str, user_message: str) -> str` that:

1. Fetches the conversation via `conversation_repo.get(conversation_id)` -- raises `BookError(NOT_FOUND)` if missing
2. Persists the user message as a `ChatMessage` with role `USER`
3. Loads conversation history via `chat_message_repo.get_by_conversation(conversation_id)`
4. Builds prompt messages via `ConversationContextStrategy.build_context()`
5. Enters the agent loop (see CA-2), passing `on_event` to the retrieval strategy
6. Persists the assistant response as a `ChatMessage` with role `ASSISTANT`
7. Returns the assistant response text

If `on_event` is provided, events are emitted at key moments:

- After each tool invocation by the retrieval strategy: emits `ToolInvocationEvent`
- After each tool result is received: emits `ToolResultEvent`
- After each LLM call that returns token usage: emits `TokenUsageEvent`

If `on_event` is `None`, no events are emitted (no-op).

#### Scenario: Single-turn response without retrieval

- **WHEN** `execute` is called and the LLM responds with text directly (no tool invocation)
- **THEN** the user message is persisted, the LLM response is persisted, and the response text is returned

#### Scenario: Response with tool-use retrieval

- **WHEN** `execute` is called and the LLM invokes the `search_book` tool
- **THEN** the search is executed, results are appended as a tool_result message, the LLM is called again, and the final text response is returned

#### Scenario: Conversation not found

- **WHEN** `execute` is called with a non-existent conversation ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

#### Scenario: LLM failure propagates

- **WHEN** the LLM API call fails during the agent loop
- **THEN** an `LLMError` is raised (user message is already persisted; no assistant message is persisted)

#### Scenario: Events emitted during tool-use turn

- **WHEN** `execute()` is called with `on_event` set and the LLM invokes a tool
- **THEN** `ToolInvocationEvent`, `ToolResultEvent`, and `TokenUsageEvent` are emitted via the callback

#### Scenario: No events when callback is None

- **WHEN** `execute()` is called with `on_event=None`
- **THEN** no events are emitted; behavior is otherwise identical

#### Scenario: Token usage emitted on direct response

- **WHEN** the LLM responds directly without tool use
- **THEN** only `TokenUsageEvent` is emitted (no tool events)

### CA-2: Agent loop executes tool invocations iteratively

The agent loop SHALL:

1. Build the message list using `ConversationContextStrategy.build_context()` with persisted history plus the current turn
2. Call `ChatProvider.chat_with_tools()` with the messages and tool definitions from `RetrievalStrategy.build_tool_definitions()`
3. If the response contains a `tool_invocation`:
   a. Execute the tool (call `SearchBooksUseCase.execute()` with the tool arguments)
   b. Format the search results as a tool result string (chunk content with page references)
   c. Append a `tool_result` `PromptMessage` to the message list
   d. Persist the tool result as a `ChatMessage` with role `TOOL_RESULT`
   e. Call `chat_with_tools()` again with the updated messages
4. If the response contains `text`: return the text and exit the loop
5. The loop SHALL have a maximum iteration limit (default: 3) to prevent infinite tool-use loops. If the limit is reached without a text response, raise `LLMError`.

#### Scenario: Direct text response (no tool use)

- **WHEN** the LLM responds with text on the first call
- **THEN** the loop exits immediately with the text response

#### Scenario: Single tool invocation then text

- **WHEN** the LLM invokes `search_book` on the first call and responds with text on the second call
- **THEN** the search is executed, results are appended, and the final text is returned

#### Scenario: Multiple tool invocations

- **WHEN** the LLM invokes tools on consecutive calls
- **THEN** each tool is executed and results appended until the LLM returns text or the iteration limit is reached

#### Scenario: Iteration limit prevents infinite loop

- **WHEN** the LLM continuously invokes tools without returning text
- **THEN** an `LLMError` is raised after the maximum iteration limit is reached

### CA-3: RetrievalStrategy protocol controls retrieval behavior

The domain layer SHALL define a `RetrievalStrategy` protocol in `domain/protocols.py` with method:

- `execute(chat_provider, messages, tools, search_fn, on_event=None) -> tuple[str, list[ChatMessage]]` -- runs the retrieval loop with optional event emission

The `on_event` parameter is passed through from `ChatWithBookUseCase` so the strategy can emit `ToolInvocationEvent` and `ToolResultEvent` during its internal loop.

#### Scenario: Tool-use strategy provides search_book tool

- **WHEN** `build_tool_definitions()` is called on the default tool-use strategy
- **THEN** a list containing a `ToolDefinition` for `search_book` is returned with appropriate parameter schema

#### Scenario: Always-retrieve strategy provides no tools

- **WHEN** `build_tool_definitions()` is called on the always-retrieve fallback strategy
- **THEN** an empty list is returned (retrieval is performed unconditionally, not via tool-use)

### CA-4: ToolUseRetrievalStrategy is the default implementation

The application layer SHALL provide a `ToolUseRetrievalStrategy` class that implements `RetrievalStrategy`. It SHALL:

- Return a `ToolDefinition` for `search_book` with parameters: `query` (str, required -- the search query) and `top_k` (int, optional, default 5 -- number of results)
- Execute the tool by calling `SearchBooksUseCase.execute()` with the extracted arguments
- Format results as text with page references: each chunk labeled with `[Pages X-Y]` followed by content, joined by double newlines
- Emit `ToolInvocationEvent` before executing each tool and `ToolResultEvent` after receiving results (when `on_event` is provided)
- Emit `TokenUsageEvent` after each LLM call that returns `ChatResponse.usage`

#### Scenario: search_book tool definition

- **WHEN** `build_tool_definitions()` is called
- **THEN** the returned `ToolDefinition` has `name="search_book"`, a description explaining it searches the book, and a JSON Schema for `query` (required string) and `top_k` (optional integer)

#### Scenario: Tool execution returns formatted results

- **WHEN** `execute_tool` is called with a valid `search_book` invocation
- **THEN** the search is executed and results are returned as formatted text with `[Pages X-Y]` labels

#### Scenario: Tool execution with no results

- **WHEN** `execute_tool` is called and the search returns no results
- **THEN** a message indicating "No relevant passages found." is returned

### CA-5: ConversationContextStrategy protocol controls context building

The domain layer SHALL define a `ConversationContextStrategy` protocol in `domain/protocols.py` with method:

- `build_context(messages: list[ChatMessage], system_prompt: str) -> list[PromptMessage]` -- converts conversation history into prompt messages for the LLM, prepending the system prompt

#### Scenario: Context building with history

- **WHEN** `build_context` is called with a list of chat messages and a system prompt
- **THEN** a list of `PromptMessage` objects is returned starting with the system prompt

### CA-6: FullHistoryContextStrategy is the default implementation

The application layer SHALL provide a `FullHistoryContextStrategy` class that implements `ConversationContextStrategy`. It SHALL:

- Include a system message as the first `PromptMessage`
- Convert `ChatMessage` entities to `PromptMessage` objects preserving role and content
- Cap the history at `max_messages` (configurable, excluding the system message)
- When capped, keep the most recent `max_messages` messages (drop oldest first)
- Include `TOOL_RESULT` messages in the context (they are part of the conversation flow)

#### Scenario: Full history within limit

- **WHEN** `build_context` is called with 5 messages and `max_messages=20`
- **THEN** all 5 messages are included after the system prompt

#### Scenario: History exceeds limit

- **WHEN** `build_context` is called with 30 messages and `max_messages=20`
- **THEN** only the 20 most recent messages are included after the system prompt

#### Scenario: Tool result messages preserved

- **WHEN** `build_context` is called with messages containing `TOOL_RESULT` role
- **THEN** tool result messages are included in the output with role `"tool_result"`

### CA-7: Prompt assembly uses conversation system prompt

The `ChatWithBookUseCase` SHALL load the system prompt from `prompts_dir / "conversation_system_prompt.md"`. The system prompt SHALL be passed to `ConversationContextStrategy.build_context()` as the `system_prompt` parameter.

#### Scenario: System prompt loaded from template

- **WHEN** the use case initializes a conversation turn
- **THEN** the system prompt is loaded from `conversation_system_prompt.md`

#### Scenario: Missing prompt template raises error

- **WHEN** the prompt template file does not exist
- **THEN** a `FileNotFoundError` or equivalent error is raised

### CA-8: Tool result messages are persisted

Tool result messages (containing search results returned to the LLM) SHALL be persisted as `ChatMessage` entities with role `TOOL_RESULT`. They are part of the conversation history and are included in subsequent context builds.

#### Scenario: Tool result persisted in conversation

- **WHEN** the agent executes a tool and receives results
- **THEN** a `ChatMessage` with role `TOOL_RESULT` and the formatted results as content is saved

#### Scenario: Tool results appear in subsequent context

- **WHEN** a follow-up message is sent after a tool-use turn
- **THEN** the persisted tool result messages appear in the conversation context

### CA-9: ChatEvent value objects for observability

The domain layer SHALL define the following frozen dataclasses in `domain/chat_event.py`:

- `ToolInvocationEvent(tool_name: str, arguments: dict[str, object])` — emitted when the retrieval strategy invokes a tool
- `ToolResultEvent(query: str, result_count: int, results: list[SearchResult])` — emitted when a tool invocation returns search results
- `TokenUsageEvent(input_tokens: int, output_tokens: int)` — emitted when an LLM call completes with token usage data

`ChatEvent` SHALL be a type alias: `ChatEvent = ToolInvocationEvent | ToolResultEvent | TokenUsageEvent`

#### Scenario: ToolInvocationEvent creation

- **WHEN** a `ToolInvocationEvent` is created with `tool_name="search_book"` and `arguments={"query": "test"}`
- **THEN** the event is a frozen dataclass with those fields

#### Scenario: TokenUsageEvent creation

- **WHEN** a `TokenUsageEvent` is created with `input_tokens=100` and `output_tokens=50`
- **THEN** the event is a frozen dataclass with those fields

### CA-10: Generic LLM-as-judge test utility

The test infrastructure SHALL provide a `judge_response` function in `tests/helpers/llm_judge.py` with the signature:

- `judge_response(chat_provider: ChatProvider, actual: str, expected: str) -> bool`

The function is domain-agnostic. It sends a single `chat()` call with a judge prompt containing the `actual` response and the `expected` behavior description. It parses the first word of the judge's reply as the verdict (`YES` = match, `NO` = mismatch) and returns `True` when the verdict is `YES`.

#### Scenario: Response matches expected behavior

- **WHEN** `judge_response` is called with an `actual` response that satisfies the `expected` criteria
- **THEN** the function returns `True`

#### Scenario: Response violates expected behavior

- **WHEN** `judge_response` is called with an `actual` response that violates the `expected` criteria
- **THEN** the function returns `False`

### CA-11: Spoiler prevention integration test — search-bounded response

An integration test SHALL exercise `ChatWithBookUseCase` end-to-end with a pre-built SQLite fixture database (`shared/fixtures/1984_embedded.db`) containing *1984* with chunks and embeddings. The test:

1. Copies the fixture DB to `tmp_path`
2. Opens it with `Database(path, enable_vec=True)`
3. Sets `book.current_page` to a natural chapter boundary
4. Creates a fresh `Conversation` for the book
5. Wires `ChatWithBookUseCase` with real `ChatProvider` (Anthropic), real `ToolUseRetrievalStrategy`, real `FullHistoryContextStrategy`, real `SearchBooksUseCase`, and real SQLite repositories
6. Calls `execute(conversation_id, question)` with a question about early-book content
7. Evaluates the response with `judge_response` using a pre-decided expected-behavior description
8. Asserts the judge returns `True`

The test is marked `@pytest.mark.integration` and is skipped when `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is not set. Both are required: Anthropic for the chat agent, OpenAI for query embedding at search time.

#### Scenario: Agent answers from early-book content without spoilers

- **WHEN** the reader's `current_page` is set to a chapter boundary and the user asks about content from early pages
- **THEN** the agent responds using retrieved passages from within the page boundary, and the judge confirms the response does not leak content beyond `current_page`

### CA-12: Spoiler prevention integration test — parametric knowledge refusal

An integration test SHALL exercise the same pipeline as CA-11 but with a question that probes for late-book content (e.g., "How does the book end?"). Because `current_page` restricts search results to early pages, the search tool returns no relevant passages for the ending. The test verifies the agent refuses to answer from parametric knowledge.

#### Scenario: Agent refuses to reveal late-book content

- **WHEN** the reader's `current_page` is set to an early chapter boundary and the user asks about the book's ending
- **THEN** the agent does not reveal plot events beyond the reader's position, and the judge confirms the response contains no spoilers
