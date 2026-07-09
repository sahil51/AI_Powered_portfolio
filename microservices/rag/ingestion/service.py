from rag.embeddings.service import EmbeddingService


class IngestionService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def ingest_document(self, content: str, metadata: dict) -> str:
        embedding = await self.embedding_service.embed_text(content)
        doc_id = await self._store_document(content, embedding, metadata)
        return doc_id

    async def _store_document(self, content: str, embedding: list[float], metadata: dict) -> str:
        return "sample-doc-id"
