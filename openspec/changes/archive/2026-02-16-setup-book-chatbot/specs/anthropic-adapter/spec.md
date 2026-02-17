# anthropic-adapter

Delta spec for the Anthropic SDK adapter. Adds `chat_with_tools()` implementation using Anthropic's native tool-use API.

## ADDED Requirements

### AA-2: Anthropic adapter implements chat_with_tools()

The Anthropic `ChatProvider` adapter SHALL implement `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` using the Anthropic Python SDK's `messages.create()` API with the `tools` parameter.

#### Scenario: Tool definitions mapped to Anthropic format

- **WHEN** `chat_with_tools()` is called with `ToolDefinition` objects
- **THEN** each `ToolDefinition` is mapped to Anthropic's tool format: `{"name": td.name, "description": td.description, "input_schema": td.parameters}`

#### Scenario: LLM returns text response

- **WHEN** the Anthropic API responds with a text content block (no `tool_use` block)
- **THEN** a `ChatResponse(text=<response_text>, tool_invocation=None)` is returned

#### Scenario: LLM returns tool_use response

- **WHEN** the Anthropic API responds with a `tool_use` content block
- **THEN** a `ChatResponse(text=None, tool_invocation=ToolInvocation(tool_name=<name>, arguments=<input>))` is returned

#### Scenario: System messages extracted

- **WHEN** `chat_with_tools()` is called with messages containing a system prompt
- **THEN** system messages are extracted and passed via the `system` parameter (same as `chat()`)

#### Scenario: tool_result messages mapped to Anthropic format

- **WHEN** `chat_with_tools()` is called with a `PromptMessage(role="tool_result", ...)` in the message list
- **THEN** the message is mapped to Anthropic's tool result format for the messages array

#### Scenario: API errors wrapped in LLMError

- **WHEN** the Anthropic API call fails during `chat_with_tools()`
- **THEN** an `LLMError` with code `API_CALL_FAILED` is raised

### AA-3: Anthropic adapter handles empty tools list

When `chat_with_tools()` is called with an empty `tools` list, the adapter SHALL omit the `tools` parameter from the Anthropic API call, effectively making it equivalent to a regular `chat()` call.

#### Scenario: Empty tools list omits tools parameter

- **WHEN** `chat_with_tools(messages, tools=[])` is called
- **THEN** the Anthropic API is called without the `tools` parameter

#### Scenario: Empty tools list returns text response

- **WHEN** `chat_with_tools(messages, tools=[])` is called
- **THEN** a `ChatResponse` with `text` populated is returned (no tool invocation possible)

## MODIFIED Requirements

### AA-1: Anthropic adapter implements ChatProvider (MODIFIED)

The infrastructure layer provides a `ChatProvider` adapter in `infra/llm/anthropic.py` that uses the Anthropic Python SDK's `messages.create()` API. Default model: `claude-sonnet-4-5-20250514`.

- System messages (`PromptMessage(role="system", ...)`) are extracted from the message list and passed via the `system` parameter, not in the messages array
- API errors are wrapped in `LLMError` with code `API_CALL_FAILED`
- The `model_name` property returns the configured model name string
- The adapter now implements both `chat()` and `chat_with_tools()` methods

**Changes from original:**
- The adapter MUST now also implement `chat_with_tools()` (see AA-2)
- The class still implements the full `ChatProvider` protocol which now includes both methods

#### Scenario: Adapter implements full ChatProvider protocol

- **WHEN** the Anthropic adapter is inspected
- **THEN** it implements `chat()`, `chat_with_tools()`, and the `model_name` property

#### Scenario: Existing chat() method unchanged

- **WHEN** `chat()` is called on the Anthropic adapter
- **THEN** it behaves identically to the pre-change implementation
