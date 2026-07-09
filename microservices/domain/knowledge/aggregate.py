from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.events import (
    KnowledgeArchived,
    KnowledgeChunkAdded,
    KnowledgeChunked,
    KnowledgeChunkRemoved,
    KnowledgeDeleted,
    KnowledgeEvent,
)
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.policies import KnowledgePolicies, default_knowledge_policies
from domain.knowledge.state import KnowledgeStateMachine, KnowledgeStatus
from domain.knowledge.value_objects import (
    ChunkingStrategy,
    DocumentId,
    DocumentSource,
    DocumentType,
    KnowledgeVersion,
)


@dataclass
class KnowledgeDocument:
    document_id: DocumentId = field(default_factory=DocumentId)
    title: str = ""
    doc_type: DocumentType = DocumentType.CUSTOM
    source: DocumentSource = field(default_factory=DocumentSource)
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    state_machine: KnowledgeStateMachine = field(default_factory=KnowledgeStateMachine)
    policies: KnowledgePolicies = field(default_factory=lambda: default_knowledge_policies)
    metadata: KnowledgeMetadata = field(default_factory=KnowledgeMetadata)
    events: list[KnowledgeEvent] = field(default_factory=list)
    version: KnowledgeVersion = field(default_factory=KnowledgeVersion)
    checksum: str = ""
    correlation_id: str = ""
    tags: list[str] = field(default_factory=list)
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None
    embedded_at: datetime | None = None
    indexed_at: datetime | None = None

    @property
    def status(self) -> KnowledgeStatus:
        return self.state_machine.current_state

    @property
    def is_active(self) -> bool:
        return self.state_machine.is_active()

    @property
    def is_terminal(self) -> bool:
        return self.state_machine.is_terminal()

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def total_tokens(self) -> int:
        return sum(c.token_count for c in self.chunks)

    @property
    def total_characters(self) -> int:
        return sum(c.character_count for c in self.chunks)

    def _record_event(self, event: KnowledgeEvent) -> None:
        self.events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def upload(self) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.UPLOADED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            self._record_event(event)
        self._touch()

    def start_processing(self) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.PROCESSING)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            self._record_event(event)
        self._touch()

    def chunk(
        self,
        chunk_count: int = 0,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
    ) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.CHUNKED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            if isinstance(event, KnowledgeChunked):
                event.chunk_count = chunk_count
                event.chunking_strategy = chunking_strategy
            self._record_event(event)
        self.processed_at = datetime.now(timezone.utc)
        self._touch()

    def embed(self) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.EMBEDDED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            self._record_event(event)
        self.embedded_at = datetime.now(timezone.utc)
        self._touch()

    def index(self) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.INDEXED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            self._record_event(event)
        self.indexed_at = datetime.now(timezone.utc)
        self._touch()

    def activate(self) -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.ACTIVE)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            self._record_event(event)
        self._touch()

    def archive(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.ARCHIVED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            if isinstance(event, KnowledgeArchived):
                event.reason = reason
            self._record_event(event)
        self._touch()

    def delete(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(KnowledgeStatus.DELETED)
        if event:
            event.document_id = str(self.document_id)
            event.correlation_id = self.correlation_id
            if isinstance(event, KnowledgeDeleted):
                event.reason = reason
            self._record_event(event)
        self._touch()

    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        self.chunks.append(chunk)
        event = KnowledgeChunkAdded(
            document_id=str(self.document_id),
            correlation_id=self.correlation_id,
            chunk_id=str(chunk.chunk_id),
            chunk_index=chunk.chunk_index,
        )
        self._record_event(event)
        self._touch()

    def remove_chunk(self, chunk_id: str) -> None:
        self.chunks = [c for c in self.chunks if str(c.chunk_id) != chunk_id]
        event = KnowledgeChunkRemoved(
            document_id=str(self.document_id),
            correlation_id=self.correlation_id,
            chunk_id=chunk_id,
        )
        self._record_event(event)
        self._touch()

    def update_checksum(self, checksum: str) -> None:
        self.checksum = checksum
        self._touch()

    def drain_events(self) -> list[KnowledgeEvent]:
        drained = list(self.events)
        self.events.clear()
        return drained
