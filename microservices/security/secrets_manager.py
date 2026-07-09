from __future__ import annotations

import os
import time

from monitoring.logger import logger
from security.exceptions import SecurityConfigurationError


class SecretsManager:
    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}
        self._rotation_times: dict[str, float] = {}
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Initializing secrets manager")
        try:
            self._load_from_env()
            self._validate_required()
            self._initialized = True
            logger.info("Secrets manager initialized")
        except Exception as e:
            raise SecurityConfigurationError(
                message="Failed to initialize secrets manager",
                detail=str(e),
            )

    def _load_from_env(self) -> None:
        secret_keys = [
            "JWT_SECRET", "GEMINI_API_KEY", "CEREBRAS_API_KEY",
            "NVIDIA_API_KEY", "HF_TOKEN", "OPENAI_API_KEY",
            "DB_PASSWORD", "REDIS_URL", "SENTRY_DSN",
            "LANGSMITH_API_KEY", "N8N_WEBHOOK_SECRET",
            "GOOGLE_CALENDAR_CREDENTIALS",
        ]
        for key in secret_keys:
            value = os.getenv(key, "")
            if value:
                self._secrets[key] = value
                self._rotation_times[key] = time.time()

    def _validate_required(self) -> None:
        required = ["JWT_SECRET"]
        missing = [key for key in required if key not in self._secrets]
        if missing:
            raise SecurityConfigurationError(
                message=f"Required secrets missing: {', '.join(missing)}",
            )

    def get_secret(self, key: str) -> str:
        if key not in self._secrets:
            raise SecurityConfigurationError(message=f"Secret {key} not found")
        return self._secrets[key]

    def set_secret(self, key: str, value: str) -> None:
        self._secrets[key] = value
        self._rotation_times[key] = time.time()
        os.environ[key] = value

    def rotate_secret(self, key: str, new_value: str) -> None:
        if key not in self._secrets:
            raise SecurityConfigurationError(message=f"Cannot rotate unknown secret {key}")
        old_value = self._secrets[key]
        if old_value == new_value:
            return
        self._secrets[key] = new_value
        self._rotation_times[key] = time.time()
        os.environ[key] = new_value
        logger.info(f"Secret {key} rotated")

    def has_secret(self, key: str) -> bool:
        return key in self._secrets

    def get_secret_age(self, key: str) -> float:
        if key not in self._rotation_times:
            return 0.0
        return time.time() - self._rotation_times[key]

    def list_secret_keys(self) -> list[str]:
        return list(self._secrets.keys())

    def validate_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for key in self._secrets:
            value = self._secrets[key]
            results[key] = len(value) > 0
        return results

    async def shutdown(self) -> None:
        self._secrets.clear()
        self._rotation_times.clear()
        self._initialized = False
