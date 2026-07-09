from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class ToolContextLayer(ContextLayer):
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "tool"

    @property
    def priority(self) -> int:
        return 6

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        results = kwargs.get("tool_results", [])
        return {
            "results": results,
            "tool_count": len(results),
            "tools_available": kwargs.get("tools_available", []),
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
