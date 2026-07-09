from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class MemoryContextLayer(ContextLayer):
    def __init__(self, enabled: bool = True, max_memories: int = 20) -> None:
        self._enabled = enabled
        self._max_memories = max_memories

    @property
    def name(self) -> str:
        return "memory"

    @property
    def priority(self) -> int:
        return 3

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        memories = kwargs.get("memories", [])
        max_mem = kwargs.get("max_memories", self._max_memories)

        profile_memories = []
        preference_memories = []
        relationship_memories = []
        meeting_memories = []
        other_memories = []

        for mem in memories[:max_mem]:
            cat = getattr(mem, "category", "")
            if hasattr(cat, "value"):
                cat = cat.value
            sc = getattr(mem, "scope", "")
            if hasattr(sc, "value"):
                sc = sc.value
            conf = getattr(mem, "confidence", "")
            if hasattr(conf, "value"):
                conf = conf.value
            imp = getattr(mem, "importance", "")
            if hasattr(imp, "value"):
                imp = imp.value
            entry = {
                "memory_id": str(getattr(mem, "memory_id", "")),
                "value": getattr(mem, "value", ""),
                "category": cat,
                "scope": sc,
                "confidence": conf,
                "importance": imp,
                "tags": getattr(mem, "tags", []),
                "updated_at": str(getattr(mem, "updated_at", "")),
            }
            if cat == "profile":
                profile_memories.append(entry)
            elif cat == "preference":
                preference_memories.append(entry)
            elif cat == "relationship":
                relationship_memories.append(entry)
            elif cat == "meeting":
                meeting_memories.append(entry)
            else:
                other_memories.append(entry)

        included = (
            len(profile_memories)
            + len(preference_memories)
            + len(relationship_memories)
            + len(meeting_memories)
            + len(other_memories)
        )
        return {
            "profile": profile_memories,
            "preferences": preference_memories,
            "relationships": relationship_memories,
            "meetings": meeting_memories,
            "other": other_memories,
            "total_count": len(memories),
            "included_count": included,
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_max_memories(self, max_memories: int) -> None:
        self._max_memories = max_memories
