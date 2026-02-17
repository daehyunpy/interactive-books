## ADDED Requirements

### Requirement: PromptMessage domain model represents an LLM message

The domain layer SHALL define a `PromptMessage` frozen dataclass in `domain/prompt_message.py` with fields: `role: str` and `content: str`. Valid roles are `"system"`, `"user"`, and `"assistant"`.

#### Scenario: Valid PromptMessage creation

- **WHEN** `PromptMessage(role="user", content="What is this about?")` is created
- **THEN** the object is created successfully with the given values

#### Scenario: PromptMessage is immutable

- **WHEN** a `PromptMessage` instance is created
- **THEN** its fields cannot be reassigned (frozen dataclass)

#### Scenario: System message

- **WHEN** `PromptMessage(role="system", content="You are a helpful assistant.")` is created
- **THEN** the object is valid with role `"system"`

### Requirement: ChatProvider protocol defines LLM chat abstraction

The domain layer SHALL define a `ChatProvider` protocol in `domain/protocols.py` with:

- A `model_name` property returning `str`
- A `chat(messages: list[PromptMessage]) → str` method that sends messages to an LLM and returns the full response text

#### Scenario: Protocol is defined in domain layer

- **WHEN** a developer imports from `domain/protocols.py`
- **THEN** `ChatProvider` is available as a Protocol class with `model_name` property and `chat` method

#### Scenario: Chat returns full response

- **WHEN** `chat(messages)` is called with a list of PromptMessage objects
- **THEN** the full LLM response is returned as a string
