from __future__ import annotations

from application.embedding.exceptions import EmbeddingValidationError
from application.embedding.models import EmbeddingConfiguration, EmbeddingRequest, EmbeddingResponse


class EmbeddingValidator:
    def validate_request(self, request: EmbeddingRequest) -> None:
        if not request.chunk_id:
            raise EmbeddingValidationError("chunk_id is required")
        if not request.text:
            raise EmbeddingValidationError("text is required")
        if not request.model:
            raise EmbeddingValidationError("model is required")

    def validate_response(self, response: EmbeddingResponse) -> bool:
        if not response.chunk_id:
            raise EmbeddingValidationError("response chunk_id is required")
        if not response.embedding and response.embedding is not None:
            raise EmbeddingValidationError("embedding must be a list")
        return True

    def validate_chunk(self, chunk_text: str) -> None:
        if not chunk_text or not chunk_text.strip():
            raise EmbeddingValidationError("Chunk text cannot be empty")

    def validate_chunks(self, chunks: list[str]) -> list[str]:
        validated: list[str] = []
        seen: set[str] = set()
        for chunk_text in chunks:
            stripped = chunk_text.strip()
            if not stripped:
                continue
            if stripped in seen:
                continue
            seen.add(stripped)
            validated.append(stripped)
        return validated

    def validate_configuration(self, config: EmbeddingConfiguration) -> None:
        if not config.model:
            raise EmbeddingValidationError("model is required")
        if config.dimensions <= 0:
            raise EmbeddingValidationError("dimensions must be positive")
        if config.max_retries < 0:
            raise EmbeddingValidationError("max_retries cannot be negative")
        if config.timeout <= 0:
            raise EmbeddingValidationError("timeout must be positive")
        if config.batch_size <= 0:
            raise EmbeddingValidationError("batch_size must be positive")
        if config.max_tokens_per_chunk <= 0:
            raise EmbeddingValidationError("max_tokens_per_chunk must be positive")
        if config.overlap_tokens < 0:
            raise EmbeddingValidationError("overlap_tokens cannot be negative")

    def validate_embedding_dimension(self, dimension: int, expected: int) -> bool:
        if expected <= 0:
            raise EmbeddingValidationError("expected dimension must be positive")
        return dimension == expected

    def is_chunk_valid(self, chunk_text: str) -> bool:
        return bool(chunk_text and chunk_text.strip())
