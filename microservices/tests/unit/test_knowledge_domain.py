from __future__ import annotations

import pytest

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.domain_service import KnowledgeDomainService
from domain.knowledge.events import (
    KnowledgeUploaded,
)
from domain.knowledge.factory import KnowledgeFactory
from domain.knowledge.lifecycle import KnowledgeLifecycle
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.state import (
    IllegalKnowledgeTransitionError,
    KnowledgeStateMachine,
    KnowledgeStatus,
)
from domain.knowledge.validator import KnowledgeValidationError, KnowledgeValidator
from domain.knowledge.value_objects import (
    ChunkId,
    DocumentId,
    DocumentType,
    EmbeddingStatus,
    KnowledgeVersion,
    compute_checksum,
)


class TestKnowledgeValueObjects:
    def test_document_id_generation(self) -> None:
        id1 = DocumentId()
        id2 = DocumentId()
        assert id1 != id2
        assert isinstance(id1.value, str)
        assert str(id1) == id1.value

    def test_document_id_equality(self) -> None:
        id1 = DocumentId()
        id2 = DocumentId()
        id1b = DocumentId()
        object.__setattr__(id1b, "value", id1.value)
        assert id1 == id1b
        assert id1 != id2

    def test_chunk_id_generation(self) -> None:
        id1 = ChunkId()
        id2 = ChunkId()
        assert id1 != id2
        assert isinstance(id1.value, str)
        assert str(id1) == id1.value

    def test_knowledge_version_default(self) -> None:
        v = KnowledgeVersion()
        assert v.value == "1.0.0"

    def test_knowledge_version_bump_major(self) -> None:
        v = KnowledgeVersion("1.2.3")
        bumped = v.bump_major()
        assert bumped.value == "2.0.0"

    def test_knowledge_version_bump_minor(self) -> None:
        v = KnowledgeVersion("1.2.3")
        bumped = v.bump_minor()
        assert bumped.value == "1.3.0"

    def test_knowledge_version_bump_patch(self) -> None:
        v = KnowledgeVersion("1.2.3")
        bumped = v.bump_patch()
        assert bumped.value == "1.2.4"

    def test_compute_checksum(self) -> None:
        text = "hello world"
        result = compute_checksum(text)
        assert isinstance(result, str)
        assert len(result) == 64
        assert result == compute_checksum(text)

    def test_document_type_values(self) -> None:
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.TXT.value == "txt"
        assert DocumentType.CUSTOM.value == "custom"
        assert DocumentType.MARKDOWN.value == "markdown"

    def test_knowledge_status_values(self) -> None:
        assert KnowledgeStatus.CREATED.value == "created"
        assert KnowledgeStatus.ACTIVE.value == "active"
        assert KnowledgeStatus.DELETED.value == "deleted"
        assert KnowledgeStatus.ARCHIVED.value == "archived"


class TestKnowledgeStateMachine:
    def test_initial_state(self) -> None:
        sm = KnowledgeStateMachine()
        assert sm.current_state == KnowledgeStatus.CREATED

    def test_valid_transition_created_to_uploaded(self) -> None:
        sm = KnowledgeStateMachine()
        event = sm.transition_to(KnowledgeStatus.UPLOADED)
        assert sm.current_state == KnowledgeStatus.UPLOADED
        assert isinstance(event, KnowledgeUploaded)

    def test_valid_transition_full_lifecycle(self) -> None:
        sm = KnowledgeStateMachine()
        assert sm.current_state == KnowledgeStatus.CREATED
        sm.transition_to(KnowledgeStatus.UPLOADED)
        assert sm.current_state == KnowledgeStatus.UPLOADED
        sm.transition_to(KnowledgeStatus.PROCESSING)
        assert sm.current_state == KnowledgeStatus.PROCESSING
        sm.transition_to(KnowledgeStatus.CHUNKED)
        assert sm.current_state == KnowledgeStatus.CHUNKED
        sm.transition_to(KnowledgeStatus.EMBEDDED)
        assert sm.current_state == KnowledgeStatus.EMBEDDED
        sm.transition_to(KnowledgeStatus.INDEXED)
        assert sm.current_state == KnowledgeStatus.INDEXED
        sm.transition_to(KnowledgeStatus.ACTIVE)
        assert sm.current_state == KnowledgeStatus.ACTIVE
        sm.transition_to(KnowledgeStatus.ARCHIVED)
        assert sm.current_state == KnowledgeStatus.ARCHIVED
        assert sm.is_terminal() is False

    def test_invalid_transition(self) -> None:
        sm = KnowledgeStateMachine()
        with pytest.raises(IllegalKnowledgeTransitionError):
            sm.transition_to(KnowledgeStatus.ACTIVE)

    def test_is_terminal(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.DELETED)
        assert sm.is_terminal() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.CREATED)
        assert sm2.is_terminal() is False

    def test_is_active(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.CREATED)
        assert sm.is_active() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.ARCHIVED)
        assert sm2.is_active() is False
        sm3 = KnowledgeStateMachine(KnowledgeStatus.DELETED)
        assert sm3.is_active() is False

    def test_can_process(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.UPLOADED)
        assert sm.can_process() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.CHUNKED)
        assert sm2.can_process() is True
        sm3 = KnowledgeStateMachine(KnowledgeStatus.CREATED)
        assert sm3.can_process() is False

    def test_can_embed(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.CHUNKED)
        assert sm.can_embed() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.EMBEDDED)
        assert sm2.can_embed() is False

    def test_can_index(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.EMBEDDED)
        assert sm.can_index() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.CHUNKED)
        assert sm2.can_index() is False

    def test_can_activate(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.INDEXED)
        assert sm.can_activate() is True
        sm2 = KnowledgeStateMachine(KnowledgeStatus.EMBEDDED)
        assert sm2.can_activate() is False

    def test_allowed_transitions(self) -> None:
        sm = KnowledgeStateMachine(KnowledgeStatus.CREATED)
        allowed = sm.allowed_transitions()
        assert KnowledgeStatus.UPLOADED in allowed
        assert KnowledgeStatus.ARCHIVED in allowed
        assert KnowledgeStatus.DELETED in allowed
        assert KnowledgeStatus.PROCESSING not in allowed


class TestKnowledgeFactory:
    def setup_method(self) -> None:
        self.factory = KnowledgeFactory()

    def test_create_document(self) -> None:
        doc = self.factory.create(title="Test Doc")
        assert doc.title == "Test Doc"
        assert doc.status == KnowledgeStatus.CREATED
        assert isinstance(doc.document_id, DocumentId)
        assert doc.doc_type == DocumentType.CUSTOM

    def test_create_document_with_title(self) -> None:
        doc = self.factory.create(title="My Knowledge Doc")
        assert doc.title == "My Knowledge Doc"

    def test_create_empty_title_raises_error(self) -> None:
        with pytest.raises(KnowledgeValidationError, match="title is required"):
            self.factory.create(title="")
        with pytest.raises(KnowledgeValidationError, match="title is required"):
            self.factory.create(title="   ")

    def test_create_with_metadata(self) -> None:
        metadata = KnowledgeMetadata(author="Test Author", description="Test desc")
        doc = self.factory.create(title="Test", metadata=metadata)
        assert doc.metadata.author == "Test Author"
        assert doc.metadata.description == "Test desc"

    def test_restore_document(self) -> None:
        doc = self.factory.restore(
            document_id="restored-123",
            title="Restored Doc",
            status="uploaded",
        )
        assert doc.title == "Restored Doc"
        assert doc.status == KnowledgeStatus.UPLOADED
        assert str(doc.document_id) == "restored-123"

    def test_restore_with_chunks(self) -> None:
        chunks_data = [
            {
                "chunk_id": "chunk-1",
                "document_id": "restored-123",
                "chunk_index": 0,
                "text": "Chunk text",
                "token_count": 10,
                "character_count": 10,
            }
        ]
        doc = self.factory.restore(
            document_id="restored-123",
            title="Restored",
            chunks=chunks_data,
        )
        assert doc.chunk_count == 1
        assert doc.chunks[0].text == "Chunk text"
        assert str(doc.chunks[0].chunk_id) == "chunk-1"


class TestKnowledgeAggregate:
    def setup_method(self) -> None:
        self.factory = KnowledgeFactory()

    def test_initial_state(self) -> None:
        doc = self.factory.create(title="Test")
        assert doc.status == KnowledgeStatus.CREATED

    def test_upload(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        assert doc.status == KnowledgeStatus.UPLOADED

    def test_start_processing(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        doc.start_processing()
        assert doc.status == KnowledgeStatus.PROCESSING

    def test_chunk(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        doc.start_processing()
        doc.chunk(chunk_count=3)
        assert doc.status == KnowledgeStatus.CHUNKED
        assert doc.processed_at is not None

    def test_embed(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        doc.start_processing()
        doc.chunk()
        doc.embed()
        assert doc.status == KnowledgeStatus.EMBEDDED
        assert doc.embedded_at is not None

    def test_index(self) -> None:
        doc = self._build_embedded()
        doc.index()
        assert doc.status == KnowledgeStatus.INDEXED
        assert doc.indexed_at is not None

    def test_activate(self) -> None:
        doc = self._build_indexed()
        doc.activate()
        assert doc.status == KnowledgeStatus.ACTIVE

    def test_archive(self) -> None:
        doc = self._build_active()
        doc.archive(reason="No longer needed")
        assert doc.status == KnowledgeStatus.ARCHIVED

    def test_delete(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        doc.delete(reason="Test delete")
        assert doc.status == KnowledgeStatus.DELETED

    def test_chunk_management(self) -> None:
        doc = self.factory.create(title="Test")
        chunk = KnowledgeChunk(text="Test content")
        doc.add_chunk(chunk)
        assert doc.chunk_count == 1
        assert chunk in doc.chunks
        doc.remove_chunk(str(chunk.chunk_id))
        assert doc.chunk_count == 0

    def test_status_property(self) -> None:
        doc = self.factory.create(title="Test")
        assert doc.status == KnowledgeStatus.CREATED
        assert doc.status == doc.state_machine.current_state

    def test_is_active_property(self) -> None:
        doc = self.factory.create(title="Test")
        assert doc.is_active is True
        doc.upload()
        doc.delete()
        assert doc.is_active is False

    def test_chunk_count(self) -> None:
        doc = self.factory.create(title="Test")
        assert doc.chunk_count == 0
        doc.add_chunk(KnowledgeChunk(text="One"))
        doc.add_chunk(KnowledgeChunk(text="Two"))
        assert doc.chunk_count == 2

    def test_drain_events(self) -> None:
        doc = self.factory.create(title="Test")
        doc.upload()
        assert len(doc.events) >= 1
        drained = doc.drain_events()
        assert len(drained) >= 1
        assert len(doc.events) == 0

    def test_invalid_transition_raises_error(self) -> None:
        doc = self.factory.create(title="Test")
        with pytest.raises(IllegalKnowledgeTransitionError):
            doc.activate()

    def _build_embedded(self) -> KnowledgeDocument:
        doc = self.factory.create(title="Test")
        doc.upload()
        doc.start_processing()
        doc.chunk()
        doc.embed()
        return doc

    def _build_indexed(self) -> KnowledgeDocument:
        doc = self._build_embedded()
        doc.index()
        return doc

    def _build_active(self) -> KnowledgeDocument:
        doc = self._build_indexed()
        doc.activate()
        return doc


class TestKnowledgeChunk:
    def test_chunk_defaults(self) -> None:
        chunk = KnowledgeChunk()
        assert isinstance(chunk.chunk_id, ChunkId)
        assert chunk.text == ""
        assert chunk.token_count == 0
        assert chunk.character_count == 0
        assert chunk.embedding_status == EmbeddingStatus.PENDING
        assert chunk.language == "en"
        assert chunk.embedding is None

    def test_is_embedded_false_when_pending(self) -> None:
        chunk = KnowledgeChunk(embedding_status=EmbeddingStatus.PENDING)
        assert chunk.is_embedded is False

    def test_is_embedded_true_when_completed(self) -> None:
        chunk = KnowledgeChunk(
            embedding_status=EmbeddingStatus.COMPLETED,
            embedding=[0.1, 0.2, 0.3],
        )
        assert chunk.is_embedded is True

    def test_is_embedded_false_when_completed_no_embedding(self) -> None:
        chunk = KnowledgeChunk(embedding_status=EmbeddingStatus.COMPLETED, embedding=None)
        assert chunk.is_embedded is False

    def test_is_empty_with_text(self) -> None:
        chunk = KnowledgeChunk(text="Some content")
        assert chunk.is_empty is False

    def test_is_empty_without_text(self) -> None:
        chunk = KnowledgeChunk(text="")
        assert chunk.is_empty is True
        chunk2 = KnowledgeChunk(text="   ")
        assert chunk2.is_empty is True

    def test_is_oversized(self) -> None:
        chunk = KnowledgeChunk(token_count=10000)
        assert chunk.is_oversized() is True
        chunk2 = KnowledgeChunk(token_count=100)
        assert chunk2.is_oversized() is False
        assert chunk2.is_oversized(max_tokens=50) is True


class TestKnowledgeValidator:
    def setup_method(self) -> None:
        self.validator = KnowledgeValidator()

    def test_validate_create_valid(self) -> None:
        self.validator.validate_create(title="Valid Title")

    def test_validate_create_empty_title(self) -> None:
        with pytest.raises(KnowledgeValidationError, match="title is required"):
            self.validator.validate_create(title="")

    def test_validate_chunk_valid(self) -> None:
        chunk = KnowledgeChunk(text="Valid content", character_count=200)
        self.validator.validate_chunk(chunk)

    def test_validate_chunk_empty(self) -> None:
        chunk = KnowledgeChunk(text="")
        with pytest.raises(KnowledgeValidationError, match="cannot be empty"):
            self.validator.validate_chunk(chunk)

    def test_validate_chunk_oversized(self) -> None:
        chunks = [KnowledgeChunk(text=str(i)) for i in range(10001)]
        with pytest.raises(KnowledgeValidationError, match="exceeds maximum"):
            self.validator.validate_chunks(chunks)


class TestKnowledgeLifecycle:
    def setup_method(self) -> None:
        self.lifecycle = KnowledgeLifecycle()

    def test_create_document(self) -> None:
        doc = self.lifecycle.create_document(title="Lifecycle Test")
        assert doc.title == "Lifecycle Test"
        assert doc.status == KnowledgeStatus.CREATED
        assert isinstance(doc.document_id, DocumentId)

    def test_full_lifecycle_through_lifecycle(self) -> None:
        doc = self.lifecycle.create_document(title="Full Cycle")
        self.lifecycle.upload(doc)
        assert doc.status == KnowledgeStatus.UPLOADED
        self.lifecycle.start_processing(doc)
        assert doc.status == KnowledgeStatus.PROCESSING
        chunks = [KnowledgeChunk(text="Chunk 1", character_count=200)]
        self.lifecycle.chunk(doc, chunks)
        assert doc.status == KnowledgeStatus.CHUNKED
        self.lifecycle.embed(doc)
        assert doc.status == KnowledgeStatus.EMBEDDED
        self.lifecycle.index(doc)
        assert doc.status == KnowledgeStatus.INDEXED
        self.lifecycle.activate(doc)
        assert doc.status == KnowledgeStatus.ACTIVE

    def test_upload_to_activate_pipeline(self) -> None:
        doc = self.lifecycle.create_document(title="Pipeline")
        self.lifecycle.upload(doc)
        self.lifecycle.start_processing(doc)
        chunks = [KnowledgeChunk(text="Chunk 1", character_count=200)]
        self.lifecycle.chunk(doc, chunks)
        self.lifecycle.embed(doc)
        self.lifecycle.index(doc)
        self.lifecycle.activate(doc)
        assert doc.status == KnowledgeStatus.ACTIVE
        assert doc.processed_at is not None
        assert doc.embedded_at is not None
        assert doc.indexed_at is not None


class TestKnowledgeDomainService:
    def setup_method(self) -> None:
        self.service = KnowledgeDomainService()

    def test_compute_checksum(self) -> None:
        checksum = self.service.compute_document_checksum("test content")
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        assert checksum == self.service.compute_document_checksum("test content")
        assert checksum != self.service.compute_document_checksum("other content")

    def test_validate_document_health_new_document(self) -> None:
        factory = KnowledgeFactory()
        doc = factory.create(title="Health Test")
        issues = self.service.validate_document_health(doc)
        assert "no_chunks" in issues
        assert isinstance(issues, list)

    def test_validate_document_health_healthy(self) -> None:
        factory = KnowledgeFactory()
        doc = factory.create(title="Health")
        chunk = KnowledgeChunk(text="Content", checksum="chk1", token_count=10)
        doc.add_chunk(chunk)
        doc.update_checksum("chk1")
        doc.upload()
        doc.start_processing()
        doc.chunk()
        doc.embed()
        doc.index()
        doc.activate()
        issues = self.service.validate_document_health(doc)
        assert len(issues) == 0

    def test_validate_document_health_checksum_mismatch(self) -> None:
        factory = KnowledgeFactory()
        doc = factory.create(title="Health")
        chunk = KnowledgeChunk(text="Content", checksum="chunk-chk")
        doc.add_chunk(chunk)
        doc.update_checksum("doc-chk")
        issues = self.service.validate_document_health(doc)
        assert "checksum_mismatch" in issues

    def test_validate_document_health_zero_tokens(self) -> None:
        factory = KnowledgeFactory()
        doc = factory.create(title="Health")
        chunk = KnowledgeChunk(text="Content", checksum="chk1", token_count=0)
        doc.add_chunk(chunk)
        doc.update_checksum("chk1")
        issues = self.service.validate_document_health(doc)
        assert "zero_tokens" in issues
