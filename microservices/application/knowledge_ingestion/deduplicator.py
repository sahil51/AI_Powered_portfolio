from __future__ import annotations

from domain.knowledge.value_objects import compute_checksum


class KnowledgeDeduplicator:
    def __init__(self) -> None:
        self._checksum_index: dict[str, str] = {}
        self._chunk_checksums: dict[str, set[str]] = {}

    def is_duplicate(self, checksum: str, document_id: str | None = None) -> bool:
        if checksum in self._checksum_index:
            existing_id = self._checksum_index[checksum]
            if document_id is None or existing_id != document_id:
                return True
        return False

    def compute_checksum(self, content: str) -> str:
        return compute_checksum(content)

    def mark_processed(self, checksum: str, document_id: str) -> None:
        self._checksum_index[checksum] = document_id

    def find_duplicate_chunks(
        self, checksums: list[str], document_id: str | None = None
    ) -> set[int]:
        duplicate_indices: set[int] = set()
        for idx, chunk_checksum in enumerate(checksums):
            existing = self._chunk_checksums.get(chunk_checksum)
            if existing is not None:
                duplicate_indices.add(idx)
            else:
                doc_checksums = self._chunk_checksums.setdefault(chunk_checksum, set())
                doc_checksums.add(document_id or "")
        return duplicate_indices

    def register_chunk_checksum(self, checksum: str, document_id: str) -> None:
        doc_set = self._chunk_checksums.setdefault(checksum, set())
        doc_set.add(document_id)

    def deduplicate_content(self, content: str, existing_content: str | None = None) -> str:
        if existing_content is None:
            return content
        import difflib

        existing_lines = existing_content.splitlines(keepends=True)
        new_lines = content.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, existing_lines, new_lines)
        result_parts: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "replace":
                result_parts.extend(new_lines[j1:j2])
            elif tag == "delete":
                continue
            elif tag == "insert":
                result_parts.extend(new_lines[j1:j2])
        return "".join(result_parts)

    def clear(self) -> None:
        self._checksum_index.clear()
        self._chunk_checksums.clear()
