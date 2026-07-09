from __future__ import annotations

from abc import ABC, abstractmethod

from application.intent.models import IntentContext, IntentRequest, IntentResult


class IntentClassifierInterface(ABC):
    @abstractmethod
    async def classify(self, request: IntentRequest) -> IntentResult:
        ...


class IntentResolverInterface(ABC):
    @abstractmethod
    async def resolve(self, result: IntentResult, context: IntentContext) -> IntentResult:
        ...


class IntentEngineInterface(ABC):
    @abstractmethod
    async def analyze(self, request: IntentRequest) -> IntentResult:
        ...
