from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.value_objects import DocumentId, DocumentType, KnowledgeStatus


class KnowledgeRepository(Protocol):
    async def save(self, document: KnowledgeDocument) -> None:
        ...

    async def get_by_id(self, document_id: DocumentId) -> KnowledgeDocument | None:
        ...

    async def get_by_id_str(self, document_id: str) -> KnowledgeDocument | None:
        ...

    async def get_by_title(self, title: str) -> KnowledgeDocument | None:
        ...

    async def get_by_status(self, status: KnowledgeStatus, limit: int = 50) -> Sequence[KnowledgeDocument]:
        ...

    async def get_by_tags(self, tags: list[str], limit: int = 50) -> Sequence[KnowledgeDocument]:
        ...

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        doc_type: str | None = None,
    ) -> tuple[Sequence[KnowledgeDocument], int]:
        ...

    async def delete(self, document_id: DocumentId) -> None:
        ...

    async def count_by_status(self, status: KnowledgeStatus) -> int:
        ...

    async def count_by_doc_type(self, doc_type: DocumentType) -> int:
        ...
