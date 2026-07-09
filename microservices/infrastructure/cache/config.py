from dataclasses import dataclass, field

from config.settings import settings


@dataclass
class RedisConfig:
    url: str = settings.redis_url
    sentinel_enabled: bool = settings.redis_sentinel_enabled
    sentinel_master: str = settings.redis_sentinel_master
    sentinel_hosts: list[str] = field(default_factory=lambda: settings.redis_sentinel_hosts)
    sentinel_password: str = settings.redis_sentinel_password
    pool_size: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    max_retries: int = 3
    retry_delay: float = 0.5
    decode_responses: bool = True
    health_check_interval: int = 30

    @property
    def db_url(self) -> str:
        return self.url


redis_config = RedisConfig()
