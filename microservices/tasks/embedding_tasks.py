from infrastructure.queue.celery_app import celery_app
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="embeddings")
def generate_embeddings_task(self, texts: list[str]) -> list:
    return []


@celery_app.task(bind=True, base=AppBaseTask, queue="embeddings")
def index_document_task(self, content: str, metadata: dict) -> str:
    return "doc_id_placeholder"
