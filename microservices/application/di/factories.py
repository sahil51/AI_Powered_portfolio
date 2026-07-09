from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Factory(Generic[T]):
    def __init__(self, factory_fn: Callable[..., T]) -> None:
        self._fn = factory_fn

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        return self._fn(*args, **kwargs)


class AsyncFactory(Generic[T]):
    def __init__(self, factory_fn: Callable[..., Awaitable[T]]) -> None:
        self._fn = factory_fn

    async def __call__(self, *args: Any, **kwargs: Any) -> T:
        return await self._fn(*args, **kwargs)


class LazyFactory(Generic[T]):
    def __init__(self, factory_fn: Callable[..., T]) -> None:
        self._fn = factory_fn
        self._instance: T | None = None
        self._resolved = False

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        if not self._resolved:
            self._instance = self._fn(*args, **kwargs)
            self._resolved = True
        return self._instance  # type: ignore[return-value]

    def reset(self) -> None:
        self._instance = None
        self._resolved = False
