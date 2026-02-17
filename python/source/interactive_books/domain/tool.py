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
class ChatResponse:
    text: str | None = None
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
