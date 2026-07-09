import uuid

from application.embedding.models import EmbeddingProviderType, EmbeddingRequest
from infrastructure.embedding.config import EmbeddingClientConfig
from infrastructure.embedding.factory import ProviderFactory
from monitoring.logger import logger


class EmbeddingService:
    def __init__(self):
        client_config = EmbeddingClientConfig.from_settings()
        provider = ProviderFactory.create(EmbeddingProviderType.GEMINI, client_config=client_config)
        self._provider = provider
        self._model = client_config.default_model or "text-embedding-004"
        logger.info(f"EmbeddingService initialized with Gemini provider, model={self._model}")

    async def embed_text(self, text: str) -> list[float]:
        request = EmbeddingRequest(chunk_id=str(uuid.uuid4()), text=text, model=self._model)
        response = await self._provider.generate(request)
        return response.embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        requests = [EmbeddingRequest(chunk_id=str(uuid.uuid4()), text=t, model=self._model) for t in texts]
        responses = await self._provider.generate_batch(requests)
        return [r.embedding for r in responses]

