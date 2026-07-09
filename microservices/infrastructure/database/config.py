from dataclasses import dataclass
from urllib.parse import quote_plus

from config.settings import settings


@dataclass
class DatabaseConfig:
    host: str = settings.db_host
    port: int = settings.db_port
    user: str = settings.db_user
    password: str = settings.db_password
    name: str = settings.db_name
    echo: bool = settings.debug
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    ssl_enabled: bool = False
    ssl_ca_path: str | None = None
    ssl_cert_path: str | None = None
    ssl_key_path: str | None = None

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.name}"

    @property
    def ssl_args(self) -> dict:
        if not self.ssl_enabled:
            return {}
        args: dict[str, str | None] = {}
        if self.ssl_ca_path:
            args["ssl_ca"] = self.ssl_ca_path
        if self.ssl_cert_path:
            args["ssl_cert"] = self.ssl_cert_path
        if self.ssl_key_path:
            args["ssl_key"] = self.ssl_key_path
        return {"ssl": args} if args else {"ssl": "require"}


db_config = DatabaseConfig()
