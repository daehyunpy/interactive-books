# chat-tool-use

Tool-use protocol extensions for agentic conversation: `chat_with_tools()` method on `ChatProvider`, `ToolDefinition`, `ToolInvocation`, and `ChatResponse` domain value objects, and Anthropic adapter implementation. Located in `python/source/interactive_books/domain/` and `python/source/interactive_books/infra/llm/anthropic.py`.

## ADDED Requirements

### CTU-1: ToolDefinition value object

The domain layer SHALL define a `ToolDefinition` frozen dataclass in `domain/tool_use.py` with fields:

- `name` (str) -- the tool name (e.g., `"search_book"`)
- `description` (str) -- human-readable description of what the tool does
- `parameters` (dict) -- JSON Schema object describing the tool's input parameters

`ToolDefinition` is a value object with no identity. It is immutable after creation.

#### Scenario: Valid ToolDefinition creation

- **WHEN** a `ToolDefinition` is created with `name="search_book"`, a description, and a valid JSON Schema dict
- **THEN** all fields are accessible and the object is frozen

#### Scenario: ToolDefinition equality

- **WHEN** two `ToolDefinition` instances have the same `name`, `description`, and `parameters`
- **THEN** they are equal

### CTU-2: ToolInvocation value object

The domain layer SHALL define a `ToolInvocation` frozen dataclass in `domain/tool_use.py` with fields:

- `tool_name` (str) -- the name of the tool the LLM wants to invoke
- `arguments` (dict) -- the arguments the LLM provided for the tool call

`ToolInvocation` is a value object with no identity. It is immutable after creation.

#### Scenario: Valid ToolInvocation creation

- **WHEN** a `ToolInvocation` is created with `tool_name="search_book"` and `arguments={"query": "main character", "top_k": 5}`
- **THEN** all fields are accessible and the object is frozen

#### Scenario: ToolInvocation with minimal arguments

- **WHEN** a `ToolInvocation` is created with `arguments={"query": "theme"}`
- **THEN** the invocation is valid (optional parameters may be absent)

### CTU-3: ChatResponse value object

The domain layer SHALL define a `ChatResponse` frozen dataclass in `domain/tool_use.py` with fields:

- `text` (str | None) -- the LLM's text response, populated when the LLM responds with text
- `tool_invocation` (ToolInvocation | None) -- the tool the LLM wants to invoke, populated when the LLM requests a tool call

Exactly one of `text` or `tool_invocation` MUST be populated (not both, not neither). This invariant SHALL be enforced in `__post_init__`.

#### Scenario: Text-only response

- **WHEN** a `ChatResponse` is created with `text="The main character is..."` and `tool_invocation=None`
- **THEN** the response is valid and `text` is accessible

#### Scenario: Tool-invocation-only response

- **WHEN** a `ChatResponse` is created with `text=None` and a valid `ToolInvocation`
- **THEN** the response is valid and `tool_invocation` is accessible

#### Scenario: Both populated raises error

- **WHEN** a `ChatResponse` is created with both `text` and `tool_invocation` populated
- **THEN** a `ValueError` is raised

#### Scenario: Neither populated raises error

- **WHEN** a `ChatResponse` is created with both `text=None` and `tool_invocation=None`
- **THEN** a `ValueError` is raised

### CTU-4: ChatProvider.chat_with_tools() protocol method

The `ChatProvider` protocol SHALL be extended with a `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` method. This method sends messages to the LLM with tool definitions and returns a `ChatResponse` that may contain either text or a tool invocation.

The existing `chat()` method SHALL remain for backward compatibility with simple single-turn calls.

#### Scenario: LLM returns text response

- **WHEN** `chat_with_tools()` is called and the LLM decides not to use any tools
- **THEN** a `ChatResponse` with `text` populated and `tool_invocation=None` is returned

#### Scenario: LLM returns tool invocation

- **WHEN** `chat_with_tools()` is called and the LLM decides to invoke a tool
- **THEN** a `ChatResponse` with `tool_invocation` populated and `text=None` is returned

#### Scenario: Empty tools list

- **WHEN** `chat_with_tools()` is called with an empty `tools` list
- **THEN** the LLM responds as if no tools are available (equivalent to a regular `chat()` call)

### CTU-5: PromptMessage supports tool_result role

`PromptMessage` SHALL support `"tool_result"` as a valid role value in addition to `"system"`, `"user"`, and `"assistant"`. This enables passing tool execution results back to the LLM in the message list.

#### Scenario: tool_result PromptMessage creation

- **WHEN** a `PromptMessage` is created with `role="tool_result"` and content containing search results
- **THEN** the message is valid and can be included in the messages list for `chat_with_tools()`

### CTU-6: No external dependencies in domain value objects

The `ToolDefinition`, `ToolInvocation`, and `ChatResponse` value objects in `domain/tool_use.py` SHALL import only from the standard library and other domain modules. No imports from `infra/`, `app/`, or third-party packages.

#### Scenario: Domain isolation

- **WHEN** `domain/tool_use.py` is inspected
- **THEN** all imports are from the standard library or domain modules only
