from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class KnowledgeContextLayer(ContextLayer):
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "knowledge"

    @property
    def priority(self) -> int:
        return 5

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "documents": kwargs.get("documents", []),
            "chunks": kwargs.get("chunks", []),
            "query": kwargs.get("knowledge_query", ""),
            "total_results": kwargs.get("total_results", 0),
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
