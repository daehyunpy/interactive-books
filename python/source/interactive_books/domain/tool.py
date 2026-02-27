from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, object]


@dataclass(frozen=True)
class ToolInvocation:
    tool_name: str
    tool_use_id: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ChatResponse:
    text: str | None = None
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
    usage: TokenUsage | None = None


@dataclass(frozen=True)
class ToolResult:
    formatted_text: str
    query: str
    result_count: int
    results: list[object] = field(default_factory=list)
