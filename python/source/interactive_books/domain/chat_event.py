from dataclasses import dataclass, field

from interactive_books.domain.search_result import SearchResult


@dataclass(frozen=True)
class ToolInvocationEvent:
    tool_name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class ToolResultEvent:
    query: str
    result_count: int
    results: list[SearchResult] = field(repr=False)


@dataclass(frozen=True)
class TokenUsageEvent:
    input_tokens: int
    output_tokens: int


ChatEvent = ToolInvocationEvent | ToolResultEvent | TokenUsageEvent
