from celery import Celery

from infrastructure.queue.beat import beat_schedule
from infrastructure.queue.config import celery_config
from infrastructure.queue.modules import task_modules
from infrastructure.queue.routing import task_annotations, task_queues, task_routes

celery_app = Celery(
    celery_config.app_name,
    broker=celery_config.build_broker_url(),
    backend=celery_config.result_backend,
    include=task_modules,
)

celery_app.conf.update(
    task_serializer=celery_config.task_serializer,
    accept_content=celery_config.accept_content,
    result_serializer=celery_config.result_serializer,
    timezone=celery_config.timezone,
    enable_utc=celery_config.enable_utc,
    task_track_started=celery_config.task_track_started,
    task_time_limit=celery_config.task_time_limit,
    task_soft_time_limit=celery_config.task_soft_time_limit,
    worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
    task_acks_late=celery_config.task_acks_late,
    worker_prefetch_multiplier=celery_config.worker_prefetch_multiplier,
    task_create_missing_queues=celery_config.task_create_missing_queues,
    task_default_queue=celery_config.task_default_queue,
    task_default_exchange=celery_config.task_default_exchange,
    task_default_routing_key=celery_config.task_default_routing_key,
    task_always_eager=celery_config.task_always_eager,
    worker_concurrency=celery_config.worker_concurrency,
    worker_max_memory_per_child=celery_config.worker_max_memory_per_child,
    worker_send_task_events=celery_config.worker_send_task_events,
    task_send_sent_event=celery_config.task_send_sent_event,
    result_expires=celery_config.result_expires,
    result_persistent=celery_config.result_persistent,
    broker_transport_options=celery_config.broker_transport_options,
    task_queues=task_queues,
    task_routes=task_routes,
    task_annotations=task_annotations,
    beat_schedule=beat_schedule,
)
