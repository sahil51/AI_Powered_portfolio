from rag.embeddings.service import EmbeddingService


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def retrieve(self, query: str, k: int = 5) -> list[str]:
        query_embedding = await self.embedding_service.embed_text(query)
        results = await self._vector_search(query_embedding, k)
        return results

    async def _vector_search(self, query_embedding: list[float], k: int) -> list[str]:
        return ["Sample RAG result - implement with pgvector or Pinecone"]
