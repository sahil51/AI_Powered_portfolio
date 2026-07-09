from infrastructure.queue.celery_app import celery_app
from infrastructure.queue.modules import task_modules


def autodiscover_tasks() -> list[str]:
    return task_modules


def register_tasks() -> None:
    celery_app.autodiscover_tasks(task_modules, force=True)
