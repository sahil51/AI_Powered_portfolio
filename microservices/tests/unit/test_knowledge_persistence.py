from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.state import KnowledgeStateMachine
from domain.knowledge.value_objects import (
    ChunkId,
    DocumentId,
    DocumentSource,
    DocumentType,
    EmbeddingStatus,
    KnowledgeStatus,
)
from infrastructure.persistence.models import ChunkDBModel, DocumentDBModel
from infrastructure.persistence.repository import SQLAlchemyKnowledgeRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return SQLAlchemyKnowledgeRepository(mock_session)


class _MockModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestDocumentDBModel:
    def test_table_name(self):
        assert DocumentDBModel.__tablename__ == "knowledge_documents"

    def test_required_columns(self):
        columns = {c.name: c for c in DocumentDBModel.__table__.columns}
        assert "id" in columns
        assert "title" in columns
        assert "doc_type" in columns
        assert "status" in columns
        assert "tags" in columns
        assert "checksum" in columns
        assert "is_deleted" in columns


class TestChunkDBModel:
    def test_table_name(self):
        assert ChunkDBModel.__tablename__ == "knowledge_chunks"

    def test_required_columns(self):
        columns = {c.name: c for c in ChunkDBModel.__table__.columns}
        assert "id" in columns
        assert "document_id" in columns
        assert "chunk_index" in columns
        assert "text" in columns
        assert "embedding_status" in columns
        assert "embedding" in columns


class TestKnowledgeRepositorySave:
    @pytest.mark.asyncio
    async def test_save_new_document(self, repo, mock_session):
        doc = KnowledgeDocument(title="Test Doc", doc_type=DocumentType.PDF)
        mock_session.get.return_value = None
        await repo.save(doc)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_existing_document(self, repo, mock_session):
        doc_id = str(DocumentId())
        doc = KnowledgeDocument(
            document_id=DocumentId(),
            title="Test Doc",
            doc_type=DocumentType.PDF,
        )
        object.__setattr__(doc.document_id, "value", doc_id)

        existing = MagicMock()
        existing.id = doc_id
        existing.is_deleted = False
        existing.chunks = []
        mock_session.get.return_value = existing

        await repo.save(doc)
        mock_session.get.assert_called_once()
        assert existing.title == "Test Doc"

    @pytest.mark.asyncio
    async def test_save_with_chunks(self, repo, mock_session):
        doc_id = str(DocumentId())
        chunks = [
            KnowledgeChunk(
                chunk_id=ChunkId(),
                document_id=doc_id,
                chunk_index=0,
                text="chunk1",
                token_count=10,
            ),
            KnowledgeChunk(
                chunk_id=ChunkId(),
                document_id=doc_id,
                chunk_index=1,
                text="chunk2",
                token_count=20,
            ),
        ]
        doc = KnowledgeDocument(
            document_id=DocumentId(),
            title="Test Doc",
            doc_type=DocumentType.PDF,
            chunks=chunks,
        )
        object.__setattr__(doc.document_id, "value", doc_id)

        mock_session.get.return_value = None
        await repo.save(doc)
        assert mock_session.add.called
        assert mock_session.flush.called


class TestKnowledgeRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_none(self, repo, mock_session):
        mock_session.get.return_value = None
        result = await repo.get_by_id(DocumentId())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_deleted_none(self, repo, mock_session):
        model = MagicMock()
        model.is_deleted = True
        mock_session.get.return_value = model
        result = await repo.get_by_id(DocumentId())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_str(self, repo, mock_session):
        mock_session.get.return_value = None
        result = await repo.get_by_id_str("00000000-0000-0000-0000-000000000001")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_title(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        result = await repo.get_by_title("Nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_count_by_status(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result
        count = await repo.count_by_status(KnowledgeStatus.ACTIVE)
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_by_doc_type(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result
        count = await repo.count_by_doc_type(DocumentType.PDF)
        assert count == 3


class TestKnowledgeRepositoryDelete:
    @pytest.mark.asyncio
    async def test_delete_sets_is_deleted(self, repo, mock_session):
        model = MagicMock()
        model.is_deleted = False
        model.status = "active"
        mock_session.get.return_value = model

        await repo.delete(DocumentId())
        assert model.is_deleted is True
        assert model.status == KnowledgeStatus.DELETED.value
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo, mock_session):
        mock_session.get.return_value = None
        await repo.delete(DocumentId())
        mock_session.flush.assert_not_called()


class TestKnowledgeRepositoryVectorSearch:
    @pytest.mark.asyncio
    async def test_vector_search_executes_raw_sql(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.vector_search([0.1, 0.2, 0.3], top_k=5)

        mock_session.execute.assert_called_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_with_filters(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.vector_search(
            [0.1, 0.2, 0.3],
            top_k=5,
            status_filter="active",
            tags_filter=["important"],
        )
        mock_session.execute.assert_called_once()
        assert result == []


class TestKnowledgeRepositoryKeywordSearch:
    @pytest.mark.asyncio
    async def test_keyword_search_executes_raw_sql(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.keyword_search("test query", top_k=5)
        mock_session.execute.assert_called_once()
        assert result == []


class TestKnowledgeRepositoryFilterSearch:
    @pytest.mark.asyncio
    async def test_filter_search_returns_empty(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.filter_search(tags_filter=["test"], top_k=5)
        assert result == []


class TestKnowledgeRepositoryToFromDomain:
    def _create_test_doc(self):
        return KnowledgeDocument(
            document_id=DocumentId(),
            title="Test",
            doc_type=DocumentType.PDF,
            source=DocumentSource(filename="test.pdf", mime_type="application/pdf", size_bytes=1000),
            state_machine=KnowledgeStateMachine(KnowledgeStatus.ACTIVE),
            metadata=KnowledgeMetadata(author="Author"),
            tags=["tag1", "tag2"],
            checksum="abc123",
        )

    @pytest.mark.asyncio
    async def test_round_trip_produces_same_values(self, repo, mock_session):
        doc = self._create_test_doc()
        chunks = [
            KnowledgeChunk(
                chunk_id=ChunkId(),
                document_id=str(doc.document_id),
                chunk_index=0,
                text="test chunk",
                token_count=5,
                embedding_status=EmbeddingStatus.COMPLETED,
                embedding=[0.1, 0.2, 0.3],
                embedding_dimension=3,
                embedding_model="test-model",
            ),
        ]
        doc.chunks = chunks

        model = repo._to_model(doc)
        assert model.title == doc.title
        assert model.doc_type == doc.doc_type.value
        assert model.status == doc.status.value

    def test_to_model_with_all_fields(self, repo):
        doc = self._create_test_doc()
        model = repo._to_model(doc)
        assert model.source_filename == "test.pdf"
        assert model.mime_type == "application/pdf"
        assert model.size_bytes == 1000
        assert model.tags == ["tag1", "tag2"]
        assert model.author == "Author"
        assert model.checksum == "abc123"
