from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.factory import KnowledgeFactory
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.policies import KnowledgePolicies
from domain.knowledge.state import KnowledgeStateMachine
from domain.knowledge.validator import KnowledgeValidator
from domain.knowledge.value_objects import (
    ChunkId,
    ChunkingStrategy,
    DocumentId,
    DocumentSource,
    DocumentType,
    EmbeddingStatus,
    KnowledgeStatus,
    KnowledgeVersion,
)
from infrastructure.database.exceptions import RepositoryError
from infrastructure.persistence.models import ChunkDBModel, DocumentDBModel


def _uuid(val: str) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(val)


class SQLAlchemyKnowledgeRepository:
    def __init__(
        self,
        session: AsyncSession,
        factory: KnowledgeFactory | None = None,
    ) -> None:
        self._session = session
        self._factory = factory or KnowledgeFactory(KnowledgeValidator())

    @staticmethod
    def _stmt_base() -> Select:
        return select(DocumentDBModel).where(DocumentDBModel.is_deleted.is_(False))

    async def save(self, document: KnowledgeDocument) -> None:
        existing = await self._session.get(DocumentDBModel, _uuid(str(document.document_id)))
        if existing:
            await self._update_model(existing, document)
        else:
            model = self._to_model(document)
            self._session.add(model)
        await self._sync_chunks(model if not existing else existing, document)
        await self._session.flush()

    async def get_by_id(self, document_id: DocumentId) -> KnowledgeDocument | None:
        return await self.get_by_id_str(str(document_id))

    async def get_by_id_str(self, document_id: str) -> KnowledgeDocument | None:
        model = await self._session.get(DocumentDBModel, _uuid(document_id))
        if model is None or model.is_deleted:
            return None
        return await self._to_domain(model)

    async def get_by_title(self, title: str) -> KnowledgeDocument | None:
        stmt = self._stmt_base().where(DocumentDBModel.title == title)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return await self._to_domain(model)

    async def get_by_status(self, status: KnowledgeStatus, limit: int = 50) -> Sequence[KnowledgeDocument]:
        stmt = (
            self._stmt_base()
            .where(DocumentDBModel.status == status.value)
            .order_by(DocumentDBModel.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [await self._to_domain(m) for m in models]

    async def get_by_tags(self, tags: list[str], limit: int = 50) -> Sequence[KnowledgeDocument]:
        stmt = self._stmt_base()
        for tag in tags:
            stmt = stmt.where(DocumentDBModel.tags.any(tag))
        stmt = stmt.order_by(DocumentDBModel.updated_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [await self._to_domain(m) for m in models]

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        doc_type: str | None = None,
    ) -> tuple[Sequence[KnowledgeDocument], int]:
        query = self._stmt_base()
        count_query = select(func.count()).select_from(DocumentDBModel).where(DocumentDBModel.is_deleted.is_(False))

        if status:
            query = query.where(DocumentDBModel.status == status)
            count_query = count_query.where(DocumentDBModel.status == status)
        if doc_type:
            query = query.where(DocumentDBModel.doc_type == doc_type)
            count_query = count_query.where(DocumentDBModel.doc_type == doc_type)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(DocumentDBModel.updated_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        models = result.scalars().all()

        domains = [await self._to_domain(m) for m in models]
        return domains, total

    async def delete(self, document_id: DocumentId) -> None:
        model = await self._session.get(DocumentDBModel, _uuid(str(document_id)))
        if model:
            model.is_deleted = True
            model.status = KnowledgeStatus.DELETED.value
            await self._session.flush()

    async def count_by_status(self, status: KnowledgeStatus) -> int:
        stmt = (
            select(func.count())
            .select_from(DocumentDBModel)
            .where(DocumentDBModel.status == status.value, DocumentDBModel.is_deleted.is_(False))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_doc_type(self, doc_type: DocumentType) -> int:
        stmt = (
            select(func.count())
            .select_from(DocumentDBModel)
            .where(DocumentDBModel.doc_type == doc_type.value, DocumentDBModel.is_deleted.is_(False))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _to_model(self, domain: KnowledgeDocument) -> DocumentDBModel:
        return DocumentDBModel(
            id=_uuid(str(domain.document_id)),
            title=domain.title,
            doc_type=domain.doc_type.value,
            source_filename=domain.source.filename,
            source_path=domain.source.path,
            source_url=domain.source.url,
            mime_type=domain.source.mime_type,
            size_bytes=domain.source.size_bytes,
            source_encoding=domain.source.encoding,
            source_metadata=domain.source.metadata,
            status=domain.status.value,
            checksum=domain.checksum,
            correlation_id=domain.correlation_id,
            tags=domain.tags,
            author=domain.metadata.author,
            description=domain.metadata.description,
            content_type=domain.metadata.content_type,
            language=domain.metadata.language,
            doc_metadata_tags=list(domain.metadata.tags),
            custom_metadata=dict(domain.metadata.custom),
            max_chunk_size=domain.policies.max_chunk_size,
            min_chunk_size=domain.policies.min_chunk_size,
            chunk_overlap=domain.policies.default_chunk_overlap,
            chunking_strategy=domain.policies.default_chunking_strategy.value,
            auto_activate=domain.policies.auto_activate,
            enable_versioning=domain.policies.enable_versioning,
            processed_at=domain.processed_at,
            embedded_at=domain.embedded_at,
            indexed_at=domain.indexed_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            version=1,
        )

    async def _update_model(self, model: DocumentDBModel, domain: KnowledgeDocument) -> None:
        model.title = domain.title
        model.doc_type = domain.doc_type.value
        model.source_filename = domain.source.filename
        model.source_path = domain.source.path
        model.source_url = domain.source.url
        model.mime_type = domain.source.mime_type
        model.size_bytes = domain.source.size_bytes
        model.source_encoding = domain.source.encoding
        model.source_metadata = domain.source.metadata
        model.status = domain.status.value
        model.checksum = domain.checksum
        model.correlation_id = domain.correlation_id
        model.tags = domain.tags
        model.author = domain.metadata.author
        model.description = domain.metadata.description
        model.content_type = domain.metadata.content_type
        model.language = domain.metadata.language
        model.doc_metadata_tags = list(domain.metadata.tags)
        model.custom_metadata = dict(domain.metadata.custom)
        model.max_chunk_size = domain.policies.max_chunk_size
        model.min_chunk_size = domain.policies.min_chunk_size
        model.chunk_overlap = domain.policies.default_chunk_overlap
        model.chunking_strategy = domain.policies.default_chunking_strategy.value
        model.auto_activate = domain.policies.auto_activate
        model.enable_versioning = domain.policies.enable_versioning
        model.processed_at = domain.processed_at
        model.embedded_at = domain.embedded_at
        model.indexed_at = domain.indexed_at
        model.updated_at = domain.updated_at
        model.increment_version()

    async def _sync_chunks(self, model: DocumentDBModel, domain: KnowledgeDocument) -> None:
        existing_ids = {str(c.id) for c in model.chunks}
        domain_ids = {str(c.chunk_id) for c in domain.chunks}

        for cid in existing_ids - domain_ids:
            rec = next(c for c in model.chunks if str(c.id) == cid)
            await self._session.delete(rec)

        for chunk in domain.chunks:
            cid = str(chunk.chunk_id)
            if cid in existing_ids:
                db_c = next(c for c in model.chunks if str(c.id) == cid)
                db_c.chunk_index = chunk.chunk_index
                db_c.text = chunk.text
                db_c.token_count = chunk.token_count
                db_c.character_count = chunk.character_count
                db_c.section = chunk.section
                db_c.heading = chunk.heading
                db_c.chunk_metadata = chunk.metadata
                db_c.language = chunk.language
                db_c.checksum = chunk.checksum
                db_c.embedding_status = chunk.embedding_status.value
                db_c.embedding = chunk.embedding
                db_c.embedding_dimension = chunk.embedding_dimension
                db_c.embedding_model = chunk.embedding_model
                db_c.doc_version = str(chunk.version)
                db_c.updated_at = chunk.updated_at
            else:
                db_c = ChunkDBModel(
                    id=_uuid(cid),
                    document_id=_uuid(str(domain.document_id)),
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    token_count=chunk.token_count,
                    character_count=chunk.character_count,
                    section=chunk.section,
                    heading=chunk.heading,
                    chunk_metadata=chunk.metadata,
                    language=chunk.language,
                    checksum=chunk.checksum,
                    embedding_status=chunk.embedding_status.value,
                    embedding=chunk.embedding,
                    embedding_dimension=chunk.embedding_dimension,
                    embedding_model=chunk.embedding_model,
                    doc_version=str(chunk.version),
                )
                self._session.add(db_c)

    async def _to_domain(self, model: DocumentDBModel) -> KnowledgeDocument:
        doc_id = DocumentId()
        object.__setattr__(doc_id, "value", str(model.id))

        doc = KnowledgeDocument(
            document_id=doc_id,
            title=model.title or "",
            doc_type=DocumentType(model.doc_type),
            source=DocumentSource(
                filename=model.source_filename or "",
                path=model.source_path or "",
                url=model.source_url or "",
                mime_type=model.mime_type or "",
                size_bytes=model.size_bytes or 0,
                encoding=model.source_encoding or "utf-8",
                metadata=model.source_metadata or {},
            ),
            state_machine=KnowledgeStateMachine(KnowledgeStatus(model.status)),
            policies=KnowledgePolicies(
                max_chunk_size=model.max_chunk_size or 2000,
                min_chunk_size=model.min_chunk_size or 100,
                default_chunk_overlap=model.chunk_overlap or 200,
                default_chunking_strategy=ChunkingStrategy(model.chunking_strategy or "fixed_size"),
                auto_activate=model.auto_activate if model.auto_activate is not None else True,
                enable_versioning=model.enable_versioning if model.enable_versioning is not None else True,
            ),
            metadata=KnowledgeMetadata(
                author=model.author or "",
                description=model.description or "",
                source_url="",
                content_type=model.content_type or "",
                language=model.language or "en",
                tags=tuple(model.doc_metadata_tags or []),
                custom=dict(model.custom_metadata or {}),
            ),
            version=KnowledgeVersion("1.0.0"),
            checksum=model.checksum or "",
            correlation_id=model.correlation_id or "",
            tags=model.tags or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            processed_at=model.processed_at,
            embedded_at=model.embedded_at,
            indexed_at=model.indexed_at,
        )

        chunks = await self._load_chunks(model)
        doc.chunks = chunks
        return doc

    async def _load_chunks(self, model: DocumentDBModel) -> list[KnowledgeChunk]:
        stmt = (
            select(ChunkDBModel)
            .where(ChunkDBModel.document_id == model.id)
            .where(ChunkDBModel.is_deleted.is_(False))
            .order_by(ChunkDBModel.chunk_index)
        )
        result = await self._session.execute(stmt)
        db_chunks = result.scalars().all()

        chunks: list[KnowledgeChunk] = []
        for db_c in db_chunks:
            cid = ChunkId()
            object.__setattr__(cid, "value", str(db_c.id))
            chunk = KnowledgeChunk(
                chunk_id=cid,
                document_id=str(model.id),
                chunk_index=db_c.chunk_index,
                text=db_c.text or "",
                token_count=db_c.token_count or 0,
                character_count=db_c.character_count or 0,
                section=db_c.section or "",
                heading=db_c.heading or "",
                metadata=db_c.chunk_metadata or {},
                language=db_c.language or "en",
                version=KnowledgeVersion(db_c.doc_version or "1.0.0"),
                checksum=db_c.checksum or "",
                embedding_status=EmbeddingStatus(db_c.embedding_status or "pending"),
                embedding=db_c.embedding,
                embedding_dimension=db_c.embedding_dimension or 0,
                embedding_model=db_c.embedding_model or "",
                created_at=db_c.created_at,
                updated_at=db_c.updated_at,
            )
            chunks.append(chunk)
        return chunks

    async def vector_search(
        self,
        query_embedding: list[float],
        distance_metric: str = "cosine",
        top_k: int = 10,
        threshold: float = 0.0,
        status_filter: str | None = None,
        tags_filter: list[str] | None = None,
        document_ids: list[str] | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        try:
            from sqlalchemy import text as sa_text

            params: dict[str, Any] = {
                "query_embedding": str(query_embedding),
                "top_k": top_k,
                "threshold": threshold,
            }
            where_clauses = [
                "c.is_deleted = FALSE",
                "c.embedding IS NOT NULL",
                "c.embedding_status = 'completed'",
            ]
            if status_filter:
                where_clauses.append("d.status = :status_filter")
                params["status_filter"] = status_filter
            if document_ids:
                placeholders = [f":doc_id_{i}" for i in range(len(document_ids))]
                where_clauses.append(f"d.id IN ({','.join(placeholders)})")
                for i, did in enumerate(document_ids):
                    params[f"doc_id_{i}"] = did

            distance_map = {
                "cosine": "1 - (c.embedding <=> :query_embedding)",
                "l2": "1 / (1 + (c.embedding <-> :query_embedding))",
                "ip": "(c.embedding <#> :query_embedding)",
            }
            distance_expr = distance_map.get(distance_metric, "1 - (c.embedding <=> :query_embedding)")

            sql = f"""
                SELECT c.id, c.document_id, c.chunk_index, c.text, c.token_count,
                       c.character_count, c.section, c.heading, c.chunk_metadata,
                       c.language, c.checksum, c.embedding_status, c.embedding,
                       c.embedding_dimension, c.embedding_model, c.doc_version,
                       c.created_at, c.updated_at,
                       {distance_expr} AS similarity
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE {' AND '.join(where_clauses)}
                  AND {distance_expr} >= :threshold
                ORDER BY similarity DESC
                LIMIT :top_k
            """
            result = await self._session.execute(sa_text(sql), params)
            rows = result.fetchall()

            chunks_with_scores: list[tuple[KnowledgeChunk, float]] = []
            for row in rows:
                cid = ChunkId()
                object.__setattr__(cid, "value", str(row[0]))
                chunk = KnowledgeChunk(
                    chunk_id=cid,
                    document_id=str(row[1]),
                    chunk_index=row[2],
                    text=row[3] or "",
                    token_count=row[4] or 0,
                    character_count=row[5] or 0,
                    section=row[6] or "",
                    heading=row[7] or "",
                    metadata=row[8] or {},
                    language=row[9] or "en",
                    checksum=row[10] or "",
                    embedding_status=EmbeddingStatus(row[11] or "pending"),
                    embedding=row[12] if row[12] is not None else None,
                    embedding_dimension=row[13] or 0,
                    embedding_model=row[14] or "",
                    version=KnowledgeVersion(row[15] or "1.0.0"),
                    created_at=row[16],
                    updated_at=row[17],
                )
                similarity = float(row[18]) if row[18] is not None else 0.0
                chunks_with_scores.append((chunk, similarity))

            return chunks_with_scores
        except Exception as e:
            raise RepositoryError(message="Vector search failed", detail=str(e))

    async def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        status_filter: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        try:
            from sqlalchemy import text as sa_text

            params: dict[str, Any] = {
                "query": query_text,
                "top_k": top_k,
            }
            where_clauses = [
                "c.is_deleted = FALSE",
                "d.is_deleted = FALSE",
            ]
            if status_filter:
                where_clauses.append("d.status = :status_filter")
                params["status_filter"] = status_filter

            sql = f"""
                SELECT c.id, c.document_id, c.chunk_index, c.text, c.token_count,
                       c.character_count, c.section, c.heading, c.chunk_metadata,
                       c.language, c.checksum, c.embedding_status, c.embedding,
                       c.embedding_dimension, c.embedding_model, c.doc_version,
                       c.created_at, c.updated_at,
                       ts_rank(c.search_vector, plainto_tsquery('english', :query)) AS score
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE {' AND '.join(where_clauses)}
                  AND c.search_vector @@ plainto_tsquery('english', :query)
                ORDER BY score DESC
                LIMIT :top_k
            """
            result = await self._session.execute(sa_text(sql), params)
            rows = result.fetchall()

            chunks_with_scores: list[tuple[KnowledgeChunk, float]] = []
            for row in rows:
                cid = ChunkId()
                object.__setattr__(cid, "value", str(row[0]))
                chunk = KnowledgeChunk(
                    chunk_id=cid,
                    document_id=str(row[1]),
                    chunk_index=row[2],
                    text=row[3] or "",
                    token_count=row[4] or 0,
                    character_count=row[5] or 0,
                    section=row[6] or "",
                    heading=row[7] or "",
                    metadata=row[8] or {},
                    language=row[9] or "en",
                    checksum=row[10] or "",
                    embedding_status=EmbeddingStatus(row[11] or "pending"),
                    embedding=row[12] if row[12] is not None else None,
                    embedding_dimension=row[13] or 0,
                    embedding_model=row[14] or "",
                    version=KnowledgeVersion(row[15] or "1.0.0"),
                    created_at=row[16],
                    updated_at=row[17],
                )
                score = float(row[18]) if row[18] is not None else 0.0
                chunks_with_scores.append((chunk, score))

            return chunks_with_scores
        except Exception as e:
            raise RepositoryError(message="Keyword search failed", detail=str(e))

    async def filter_search(
        self,
        tags_filter: list[str] | None = None,
        status_filter: str | None = None,
        doc_type_filter: str | None = None,
        author_filter: str | None = None,
        language_filter: str | None = None,
        top_k: int = 10,
    ) -> list[tuple[KnowledgeChunk, float]]:
        query = select(ChunkDBModel).join(
            DocumentDBModel, ChunkDBModel.document_id == DocumentDBModel.id
        ).where(
            ChunkDBModel.is_deleted.is_(False),
            DocumentDBModel.is_deleted.is_(False),
        )

        if tags_filter:
            from sqlalchemy import func as sa_func
            from sqlalchemy import text as sa_text
            for tag in tags_filter:
                query = query.where(
                    sa_func.jsonb_exists(
                        sa_text("to_jsonb(knowledge_documents.tags)"),
                        tag,
                    )
                )
        if status_filter:
            query = query.where(DocumentDBModel.status == status_filter)
        if doc_type_filter:
            query = query.where(DocumentDBModel.doc_type == doc_type_filter)
        if author_filter:
            query = query.where(DocumentDBModel.author == author_filter)
        if language_filter:
            query = query.where(DocumentDBModel.language == language_filter)

        query = query.order_by(ChunkDBModel.chunk_index).limit(top_k)
        result = await self._session.execute(query)
        db_chunks = result.scalars().all()

        chunks_with_scores: list[tuple[KnowledgeChunk, float]] = []
        for db_c in db_chunks:
            cid = ChunkId()
            object.__setattr__(cid, "value", str(db_c.id))
            chunk = KnowledgeChunk(
                chunk_id=cid,
                document_id=str(db_c.document_id),
                chunk_index=db_c.chunk_index,
                text=db_c.text or "",
                token_count=db_c.token_count or 0,
                character_count=db_c.character_count or 0,
                section=db_c.section or "",
                heading=db_c.heading or "",
                metadata=db_c.chunk_metadata or {},
                language=db_c.language or "en",
                version=KnowledgeVersion(db_c.doc_version or "1.0.0"),
                checksum=db_c.checksum or "",
                embedding_status=EmbeddingStatus(db_c.embedding_status or "pending"),
                embedding=db_c.embedding,
                embedding_dimension=db_c.embedding_dimension or 0,
                embedding_model=db_c.embedding_model or "",
                created_at=db_c.created_at,
                updated_at=db_c.updated_at,
            )
            chunks_with_scores.append((chunk, 1.0))

        return chunks_with_scores
