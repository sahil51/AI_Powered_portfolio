

CACHE_VERSION = "v1"
NAMESPACE_SEPARATOR = ":"


class KeyBuilder:
    def __init__(self, namespace: str = "app", version: str = CACHE_VERSION) -> None:
        self._namespace = namespace
        self._version = version

    def build(self, *parts: str, prefix: str | None = None) -> str:
        segments: list[str] = [self._namespace, self._version]
        if prefix:
            segments.append(prefix)
        segments.extend(str(p) for p in parts)
        return NAMESPACE_SEPARATOR.join(segments)

    def lock(self, resource: str) -> str:
        return self.build("lock", resource)

    def rate_limit(self, identifier: str, window: str = "1m") -> str:
        return self.build("ratelimit", identifier, window)

    def idempotency(self, key: str) -> str:
        return self.build("idempotency", key)

    def session(self, session_id: str) -> str:
        return self.build("session", session_id)

    def memory(self, conversation_id: str, key: str = "state") -> str:
        return self.build("memory", conversation_id, key)

    def cache(self, key: str) -> str:
        return self.build("cache", key)

    def pattern(self, pattern: str) -> str:
        return self.build(pattern)

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def version(self) -> str:
        return self._version


default_key_builder = KeyBuilder()
