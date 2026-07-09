from __future__ import annotations

from abc import ABC, abstractmethod

from application.confirmation.models import ConfirmationContext, ConfirmationResult


class ConfirmationResolverInterface(ABC):
    @abstractmethod
    async def resolve(self, context: ConfirmationContext) -> ConfirmationResult:
        ...


class ConfirmationEngineInterface(ABC):
    @abstractmethod
    async def process(self, context: ConfirmationContext) -> ConfirmationResult:
        ...
