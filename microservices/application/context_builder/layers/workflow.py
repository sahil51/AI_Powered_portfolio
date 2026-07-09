from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class WorkflowContextLayer(ContextLayer):
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "workflow"

    @property
    def priority(self) -> int:
        return 4

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "workflow_id": kwargs.get("workflow_id", ""),
            "workflow_type": kwargs.get("workflow_type", ""),
            "workflow_state": kwargs.get("workflow_state", "idle"),
            "steps_completed": kwargs.get("steps_completed", 0),
            "total_steps": kwargs.get("total_steps", 0),
            "metadata": kwargs.get("workflow_metadata", {}),
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
