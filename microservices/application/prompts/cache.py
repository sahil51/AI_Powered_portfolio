from __future__ import annotations


class PromptCache:
    def __init__(self, ttl: int = 300) -> None:
        self._cache: dict[str, str] = {}
        self._ttl = ttl

    async def get(self, name: str, version: str | None = None) -> str | None:
        key = self._build_key(name, version)
        return self._cache.get(key)

    async def set(self, name: str, content: str, version: str | None = None) -> None:
        key = self._build_key(name, version)
        self._cache[key] = content

    async def invalidate(self, name: str, version: str | None = None) -> None:
        key = self._build_key(name, version)
        self._cache.pop(key, None)

    async def invalidate_all(self) -> None:
        self._cache.clear()

    def _build_key(self, name: str, version: str | None = None) -> str:
        if version:
            return f"prompt:{name}:{version}"
        return f"prompt:{name}"
