from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    async def bootstrap(self) -> None:
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...


class ConfigProvider(Provider):
    def __init__(self) -> None:
        from config.settings import settings
        self._settings = settings

    @property
    def settings(self):
        return self._settings

    async def bootstrap(self) -> None:
        from dotenv import load_dotenv
        load_dotenv()

    async def shutdown(self) -> None:
        pass


class DatabaseProvider(Provider):
    def __init__(self) -> None:
        self._initialized = False

    async def bootstrap(self) -> None:
        from infrastructure.database.session import db

        await db.initialize()
        self._initialized = True

    async def shutdown(self) -> None:
        if self._initialized:
            from infrastructure.database.session import db

            await db.dispose()
            self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized


class RedisProvider(Provider):
    def __init__(self) -> None:
        self._client = None
        self._initialized = False

    async def bootstrap(self) -> None:
        from infrastructure.cache.connection import redis_manager

        await redis_manager.initialize()
        self._client = redis_manager.client  # type: ignore[assignment]
        self._initialized = True

    async def shutdown(self) -> None:
        if self._initialized:
            from infrastructure.cache.connection import redis_manager

            await redis_manager.shutdown()
            self._client = None
            self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def client(self):
        return self._client


class LLMProvider(Provider):
    def __init__(self) -> None:
        self._initialized = False

    async def bootstrap(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized


class TaskQueueProvider(Provider):
    def __init__(self) -> None:
        self._initialized = False

    async def bootstrap(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized
