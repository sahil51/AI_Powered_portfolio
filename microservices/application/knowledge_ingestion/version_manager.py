from __future__ import annotations

from datetime import datetime
from typing import Any

from application.knowledge_ingestion.models import NormalizedDocument
from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.value_objects import KnowledgeVersion


class KnowledgeVersionManager:
    def detect_changes(
        self, existing: KnowledgeDocument, incoming: NormalizedDocument
    ) -> list[str]:
        changes: list[str] = []
        if existing.title != incoming.title:
            changes.append("title_updated")
        if existing.checksum != incoming.checksum:
            changes.append("content_updated")
        if existing.metadata.author != incoming.metadata.get("author", ""):
            changes.append("metadata_updated")
        if existing.metadata.description != incoming.metadata.get("description", ""):
            changes.append("metadata_updated")
        return changes

    def bump_version(self, current_version: str, changes: list[str]) -> str:
        try:
            parts = current_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except (IndexError, ValueError):
            return "1.0.0"

        if "content_updated" in changes:
            return f"{major}.{minor + 1}.0"
        elif "title_updated" in changes:
            return f"{major}.{minor}.{patch + 1}"
        elif "metadata_updated" in changes:
            return f"{major}.{minor}.{patch + 1}"
        return current_version

    def should_reprocess(self, existing: KnowledgeDocument, changes: list[str]) -> bool:
        return "content_updated" in changes

    def create_version_info(
        self,
        existing: KnowledgeDocument | None,
        incoming: NormalizedDocument,
    ) -> dict[str, Any]:
        changes: list[str] = []
        old_version = "0.0.0"
        if existing is not None:
            changes = self.detect_changes(existing, incoming)
            old_version = str(existing.version.value) if existing.version else "0.0.0"

        new_version = self.bump_version(old_version, changes)
        needs_reprocess = self.should_reprocess(existing, changes) if existing else True

        return {
            "old_version": old_version,
            "new_version": new_version,
            "changes": changes,
            "needs_reprocess": needs_reprocess,
            "detected_at": datetime.utcnow().isoformat(),
            "incremental_update": bool(existing) and not needs_reprocess,
        }

    def apply_version(self, doc: KnowledgeDocument, version_str: str) -> KnowledgeDocument:
        doc.version = KnowledgeVersion(value=version_str)
        doc.updated_at = datetime.utcnow()
        return doc
