from dataclasses import dataclass, field

from config.settings import settings


@dataclass
class CeleryConfig:
    app_name: str = "ai_assistant"
    broker_url: str = settings.celery_broker_url
    result_backend: str = settings.celery_result_backend
    sentinel_enabled: bool = settings.celery_redis_sentinel_enabled
    sentinel_hosts: list[str] = field(default_factory=list)
    sentinel_master: str = settings.redis_sentinel_master
    sentinel_password: str = settings.redis_sentinel_password
    task_serializer: str = "json"
    accept_content: list[str] = None
    result_serializer: str = "json"
    timezone: str = "UTC"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 300
    task_soft_time_limit: int = 240
    worker_max_tasks_per_child: int = 200
    task_acks_late: bool = True
    worker_prefetch_multiplier: int = 1
    task_create_missing_queues: bool = True
    task_default_queue: str = "default"
    task_default_exchange: str = "default"
    task_default_routing_key: str = "default"
    task_always_eager: bool = False
    worker_concurrency: int = 4
    worker_max_memory_per_child: int = 120000
    worker_send_task_events: bool = True
    task_send_sent_event: bool = True
    result_expires: int = 86400
    result_persistent: bool = True

    def __post_init__(self) -> None:
        if self.accept_content is None:
            self.accept_content = ["json"]
        if not self.sentinel_hosts and hasattr(settings, "redis_sentinel_hosts"):
            self.sentinel_hosts = settings.redis_sentinel_hosts

    @property
    def broker_transport_options(self) -> dict:
        options: dict = {
            "max_retries": 3,
            "interval_start": 0,
            "interval_step": 0.2,
            "interval_max": 0.5,
        }
        if self.sentinel_enabled:
            options["master_name"] = self.sentinel_master
            options["sentinel_kwargs"] = {}
            if self.sentinel_password:
                options["sentinel_kwargs"]["password"] = self.sentinel_password
        return options

    def build_broker_url(self) -> str:
        if not self.sentinel_enabled:
            return self.broker_url

        sentinel_hosts = ",".join(self.sentinel_hosts)
        db_num = self.broker_url.split("/")[-1] if "/" in self.broker_url else "1"
        password_part = f":{self.sentinel_password}@" if self.sentinel_password else ""
        return f"redis+sentinel://{password_part}{sentinel_hosts}/{db_num}?master_name={self.sentinel_master}"


celery_config = CeleryConfig()
