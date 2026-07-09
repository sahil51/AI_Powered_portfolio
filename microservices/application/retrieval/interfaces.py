from __future__ import annotations

from abc import ABC, abstractmethod

from application.retrieval.models import (
    RetrievalRequest,
    RetrievalResult,
    SearchFilter,
    SearchQuery,
    SearchResponse,
    SearchResult,
)


class SemanticRetriever(ABC):
    @abstractmethod
    async def search(self, request: RetrievalRequest) -> RetrievalResult:
        ...

    @abstractmethod
    async def search_batch(self, requests: list[RetrievalRequest]) -> list[RetrievalResult]:
        ...


class KeywordRetriever(ABC):
    @abstractmethod
    async def search(self, query: str, top_k: int, filter: SearchFilter | None = None) -> RetrievalResult:
        ...

    @abstractmethod
    async def search_batch(self, queries: list[str], top_k: int) -> list[RetrievalResult]:
        ...


class MetadataRetriever(ABC):
    @abstractmethod
    async def search(self, filter: SearchFilter, top_k: int) -> RetrievalResult:
        ...


class Reranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        ...

    @abstractmethod
    async def rerank_batch(
        self,
        queries: list[str],
        candidates_batch: list[list[SearchResult]],
        top_k: int,
    ) -> list[list[SearchResult]]:
        ...


class SearchService(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResponse:
        ...

    @abstractmethod
    async def search_batch(self, queries: list[SearchQuery]) -> list[SearchResponse]:
        ...


