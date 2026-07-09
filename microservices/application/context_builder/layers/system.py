from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class SystemContextLayer(ContextLayer):
    def __init__(self, system_prompt: str = "", enabled: bool = True) -> None:
        self._system_prompt = system_prompt
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "system"

    @property
    def priority(self) -> int:
        return 0

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        system_prompt = kwargs.get("system_prompt", self._system_prompt)
        return {
            "prompt": system_prompt,
            "source": kwargs.get("source", "default"),
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
