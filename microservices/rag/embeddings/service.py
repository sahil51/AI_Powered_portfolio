import hashlib
import random
from openai import AsyncOpenAI

from config.settings import settings
from monitoring.logger import logger


class EmbeddingService:
    def __init__(self):
        self.openai_configured = bool(settings.openai_api_key)
        if self.openai_configured:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            logger.warning("OPENAI_API_KEY not configured. EmbeddingService will use deterministic mock embedding fallback.")
        self.model = settings.embedding_model

    def _generate_mock_embedding(self, text: str, dimension: int = 1536) -> list[float]:
        # Generate deterministic mock embedding based on input text hash
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed = int(hasher.hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(dimension)]

    async def embed_text(self, text: str) -> list[float]:
        if not self.openai_configured:
            return self._generate_mock_embedding(text)
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.openai_configured:
            return [self._generate_mock_embedding(t) for t in texts]
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]

