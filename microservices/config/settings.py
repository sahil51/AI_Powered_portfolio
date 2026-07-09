import json
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Executive Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    db_name: str = Field(alias="DB_NAME")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")

    redis_url: str = Field("redis://127.0.0.1:6379/0", alias="REDIS_URL")
    redis_sentinel_enabled: bool = Field(False, alias="REDIS_SENTINEL_ENABLED")
    redis_sentinel_master: str = Field("mymaster", alias="REDIS_SENTINEL_MASTER")
    redis_sentinel_hosts: list[str] = Field(["127.0.0.1:26379"], alias="REDIS_SENTINEL_HOSTS")
    redis_sentinel_password: str = Field("", alias="REDIS_SENTINEL_PASSWORD")
    celery_broker_url: str = "redis://127.0.0.1:6379/1"
    celery_result_backend: str = "redis://127.0.0.1:6379/2"
    celery_redis_sentinel_enabled: bool = Field(False, alias="CELERY_REDIS_SENTINEL_ENABLED")

    jwt_secret: str = Field("super-secret-key-change-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expiry_minutes: int = 60

    llm_primary_model: str = Field("", alias="LLM_PRIMARY_MODEL")
    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")
    cerebras_api_key: str = Field("", alias="CEREBRAS_API_KEY")
    cerebras_model: str = Field("gpt-oss-120b", alias="CEREBRAS_MODEL")
    nvidia_api_key: str = Field("", alias="NVIDIA_API_KEY")
    nvidia_model: str = Field("mistralai/mistral-nemotron", alias="NVIDIA_MODEL")
    nvidia_backup_models: str = Field("", alias="NVIDIA_BACKUP_MODELS")
    nvidia_chat_url: str = Field("", alias="NVIDIA_CHAT_URL")
    hf_token: str = Field("", alias="HF_TOKEN")
    hf_model: str = Field("microsoft/FastContext-1.0-4B-SFT:featherless-ai", alias="HF_MODEL")
    hf_chat_url: str = Field("", alias="HF_CHAT_URL")
    cerebras_chat_url: str = Field("", alias="CEREBRAS_CHAT_URL")

    n8n_webhook_base_url: str = "http://localhost:5678/webhook"
    n8n_meeting_webhook_url: str = Field("", alias="N8N_MEETING_WEBHOOK_URL")

    google_calendar_credentials: str = ""
    google_calendar_id: str = "primary"

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    sentry_dsn: str = ""
    log_level: str = "INFO"

    langsmith_tracing: bool = Field(True, alias="LANGSMITH_TRACING")
    langsmith_api_key: str = Field("", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field("po", alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field("https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")

    max_conversation_history: int = 50
    short_term_memory_ttl: int = 86400
    rate_limit_per_minute: int = 30
    max_tool_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60

    n8n_webhook_secret: str = Field("", alias="N8N_WEBHOOK_SECRET")

    otlp_endpoint: str = Field("", alias="OTLP_ENDPOINT")
    prometheus_enabled: bool = Field(True, alias="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(9090, alias="PROMETHEUS_PORT")

    log_json_format: bool = Field(True, alias="LOG_JSON_FORMAT")
    log_include_correlation: bool = Field(True, alias="LOG_INCLUDE_CORRELATION")
    enable_audit_logging: bool = Field(True, alias="ENABLE_AUDIT_LOGGING")
    enable_rate_limiting: bool = Field(True, alias="ENABLE_RATE_LIMITING")
    enable_circuit_breakers: bool = Field(True, alias="ENABLE_CIRCUIT_BREAKERS")
    enable_tracing: bool = Field(True, alias="ENABLE_TRACING")
    enable_metrics: bool = Field(True, alias="ENABLE_METRICS")
    enable_health_checks: bool = Field(True, alias="ENABLE_HEALTH_CHECKS")

    encryption_enabled: bool = Field(False, alias="ENCRYPTION_ENABLED")
    evaluation_enabled: bool = Field(True, alias="EVALUATION_ENABLED")
    evaluation_default_dataset: str = Field("", alias="EVALUATION_DEFAULT_DATASET")
    evaluation_max_cases: int = Field(0, alias="EVALUATION_MAX_CASES")
    evaluation_parallel: bool = Field(False, alias="EVALUATION_PARALLEL")
    evaluation_timeout_seconds: float = Field(300.0, alias="EVALUATION_TIMEOUT_SECONDS")
    production_validation_enabled: bool = Field(True, alias="PRODUCTION_VALIDATION_ENABLED")
    webhook_max_timestamp_age: int = Field(300, alias="WEBHOOK_MAX_TIMESTAMP_AGE")
    rate_limit_burst_multiplier: int = Field(2, alias="RATE_LIMIT_BURST_MULTIPLIER")
    max_payload_size_bytes: int = Field(1048576, alias="MAX_PAYLOAD_SIZE_BYTES")

    @field_validator("redis_sentinel_hosts", mode="before")
    @classmethod
    def parse_sentinel_hosts(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
