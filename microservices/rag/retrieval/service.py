from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from rag.embeddings.service import EmbeddingService


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, session_factory=None):
        self.embedding_service = embedding_service
        self._session_factory = session_factory

    async def retrieve(self, query: str, k: int = 5) -> list[str]:
        query_embedding = await self.embedding_service.embed_text(query)
        results = await self._vector_search(query_embedding, k)
        return results

    async def _vector_search(self, query_embedding: list[float], k: int) -> list[str]:
        if not self._session_factory:
            return []

        try:
            async with self._session_factory() as session:
                sql = sa_text("""
                    SELECT c.text, 1 - (c.embedding <=> :query_embedding) AS similarity
                    FROM knowledge_chunks c
                    JOIN knowledge_documents d ON d.id = c.document_id
                    WHERE c.is_deleted = FALSE
                      AND c.embedding IS NOT NULL
                      AND c.embedding_status = 'completed'
                      AND d.is_deleted = FALSE
                    ORDER BY similarity DESC
                    LIMIT :top_k
                """)
                result = await session.execute(sql, {
                    "query_embedding": str(query_embedding),
                    "top_k": k,
                })
                rows = result.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            from monitoring.logger import logger
            logger.warning(f"Vector search failed: {e}")
            return []
