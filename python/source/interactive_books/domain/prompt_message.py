from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interactive_books.domain.tool import ToolInvocation


@dataclass(frozen=True)
class PromptMessage:
    role: str
    content: str
    tool_use_id: str | None = None
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
