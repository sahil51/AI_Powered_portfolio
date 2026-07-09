from __future__ import annotations

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.value_objects import KnowledgeStatus, compute_checksum


class KnowledgeDomainService:
    def compute_document_checksum(self, text: str) -> str:
        return compute_checksum(text)

    def detect_changes(
        self,
        old_doc: KnowledgeDocument,
        new_doc: KnowledgeDocument,
    ) -> list[str]:
        changes: list[str] = []
        if old_doc.title != new_doc.title:
            changes.append("title")
        if old_doc.doc_type != new_doc.doc_type:
            changes.append("doc_type")
        if old_doc.checksum != new_doc.checksum:
            changes.append("content")
        if old_doc.chunk_count != new_doc.chunk_count:
            changes.append("chunks")
        if old_doc.total_tokens != new_doc.total_tokens:
            changes.append("tokens")
        return changes

    def merge_chunks(
        self,
        existing_chunks: list[KnowledgeChunk],
        new_chunks: list[KnowledgeChunk],
    ) -> list[KnowledgeChunk]:
        seen_ids = {str(c.chunk_id) for c in existing_chunks}
        merged = list(existing_chunks)
        for chunk in new_chunks:
            if str(chunk.chunk_id) not in seen_ids:
                merged.append(chunk)
                seen_ids.add(str(chunk.chunk_id))
        merged.sort(key=lambda c: c.chunk_index)
        return merged

    def validate_document_health(self, document: KnowledgeDocument) -> list[str]:
        issues: list[str] = []
        if document.is_terminal:
            return issues
        if document.chunk_count == 0:
            issues.append("no_chunks")
        if document.checksum and any(
            c.checksum and c.checksum != document.checksum for c in document.chunks
        ):
            issues.append("checksum_mismatch")
        if document.total_tokens == 0 and document.chunk_count > 0:
            issues.append("zero_tokens")
        if document.status == KnowledgeStatus.ACTIVE:
            if document.processed_at is None:
                issues.append("missing_processed_at")
            if document.embedded_at is None:
                issues.append("missing_embedded_at")
            if document.indexed_at is None:
                issues.append("missing_indexed_at")
        return issues
