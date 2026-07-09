from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from application.knowledge_context.models import (
    AssembledContext,
    ChunkSelectionStrategy,
    CompressionStrategy,
    KnowledgeContextChunk,
    KnowledgeContextConfig,
    KnowledgeContextResult,
    TokenBudget,
)
from domain.knowledge.chunk import KnowledgeChunk


class KnowledgeContextProvider(ABC):
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        config: KnowledgeContextConfig,
        correlation_id: str = "",
    ) -> KnowledgeContextResult:
        ...

    @abstractmethod
    async def retrieve_by_ids(
        self,
        chunk_ids: list[str],
        correlation_id: str = "",
    ) -> list[KnowledgeChunk]:
        ...


class KnowledgeContextAssembler(ABC):
    @abstractmethod
    async def assemble(
        self,
        result: KnowledgeContextResult,
        budget: TokenBudget,
        config: KnowledgeContextConfig,
    ) -> AssembledContext:
        ...

    @abstractmethod
    def select_chunks(
        self,
        chunks: list[KnowledgeContextChunk],
        strategy: ChunkSelectionStrategy,
        max_chunks: int,
    ) -> list[KnowledgeContextChunk]:
        ...


class KnowledgeContextCompressor(ABC):
    @abstractmethod
    def compress(
        self,
        text: str,
        strategy: CompressionStrategy,
        max_tokens: int,
    ) -> tuple[str, int]:
        ...

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        ...


class ContextCacheStrategy(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def invalidate_for_document(self, document_id: str) -> None:
        ...


class ContextSecurityPolicy(Protocol):
    def can_access_document(self, document_id: str, tenant_id: str) -> bool:
        ...

    def filter_by_visibility(self, chunks: list[KnowledgeContextChunk]) -> list[KnowledgeContextChunk]:
        ...
