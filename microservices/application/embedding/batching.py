from __future__ import annotations

import time
from dataclasses import dataclass

from application.embedding.chunking import ChunkerStrategy
from application.embedding.exceptions import EmbeddingError, EmbeddingTimeoutError
from application.embedding.models import EmbeddingBatchResult, EmbeddingRequest
from domain.knowledge.aggregate import KnowledgeDocument


@dataclass
class BatchProgress:
    completed: int = 0
    failed: int = 0
    total: int = 0

    @property
    def remaining(self) -> int:
        return self.total - self.completed - self.failed


class EmbeddingBatchProcessor:
    def __init__(self, cancelled: bool = False) -> None:
        self._progress = BatchProgress()
        self._cancelled = cancelled

    @property
    def progress(self) -> BatchProgress:
        return self._progress

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True

    def process_document(
        self,
        document: KnowledgeDocument,
        chunker: ChunkerStrategy,
        batch_size: int = 32,
        max_retries: int = 3,
    ) -> EmbeddingBatchResult:
        start = time.monotonic()
        try:
            text = " ".join(chunk.text for chunk in document.chunks) if document.chunks else ""
            if not text.strip():
                return EmbeddingBatchResult(
                    document_id=str(document.document_id),
                    success=False,
                    error="Document has no content to embed",
                )

            result = chunker.chunk(text)
            chunks = result.chunks

            requests = [
                EmbeddingRequest(
                    chunk_id=f"{document.document_id}_{i}",
                    text=chunk_text,
                )
                for i, chunk_text in enumerate(chunks)
            ]

            batches = self.split_into_batches(requests, batch_size)
            all_embeddings: list[list[float]] = []
            self._progress.total = len(requests)

            for batch in batches:
                if self._cancelled:
                    break

                for attempt in range(max_retries + 1):
                    try:
                        embeddings = self._call_provider_batch(batch)
                        all_embeddings.extend(embeddings)
                        self._progress.completed += len(batch)
                        break
                    except EmbeddingTimeoutError:
                        if attempt >= max_retries:
                            self._progress.failed += len(batch)
                            raise

            latency = (time.monotonic() - start) * 1000
            return EmbeddingBatchResult(
                document_id=str(document.document_id),
                chunks=chunks,
                embeddings=all_embeddings,
                success=len(all_embeddings) == len(requests),
                latency_ms=latency,
            )
        except EmbeddingError:
            latency = (time.monotonic() - start) * 1000
            return EmbeddingBatchResult(
                document_id=str(document.document_id),
                success=False,
                latency_ms=latency,
            )

    def process_documents(
        self,
        documents: list[KnowledgeDocument],
        chunker: ChunkerStrategy,
        batch_size: int = 32,
        max_retries: int = 3,
    ) -> list[EmbeddingBatchResult]:
        results: list[EmbeddingBatchResult] = []
        for doc in documents:
            if self._cancelled:
                break
            result = self.process_document(doc, chunker, batch_size, max_retries)
            results.append(result)
        return results

    def split_into_batches(
        self,
        requests: list[EmbeddingRequest],
        batch_size: int,
    ) -> list[list[EmbeddingRequest]]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        return [requests[i:i + batch_size] for i in range(0, len(requests), batch_size)]

    def _call_provider_batch(self, batch: list[EmbeddingRequest]) -> list[list[float]]:
        raise NotImplementedError("Subclasses must implement provider calls")
