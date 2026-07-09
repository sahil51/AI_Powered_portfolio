from __future__ import annotations

import json
import logging
import re
import sys
from typing import Any

from observability.models import LogContext

SENSITIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w-]+['\"]?"),
    re.compile(r"(?i)(secret|password|token|credential)\s*[:=]\s*['\"]?\S+['\"]?"),
    re.compile(r"(?i)(authorization|bearer)\s+\S+"),
    re.compile(r"\b\d{16}\b"),
    re.compile(r"(?i)(ssn|social.security)\s*[:=]\s*\d{3}[-]?\d{2}[-]?\d{4}"),
]


def mask_sensitive_data(data: str) -> str:
    for pattern in SENSITIVE_PATTERNS:
        data = pattern.sub(lambda m: m.group(0)[:m.group(0).find(m.group(0)[-1])] + "***", data)
    return data


class JSONFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra_keys = set(record.__dict__.keys()) - {
            "name", "msg", "args", "levelname", "levelno",
            "pathname", "filename", "module", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread",
            "threadName", "process", "processName",
            "taskName",
        }
        for key in extra_keys:
            value = getattr(record, key, "")
            if isinstance(value, str):
                value = mask_sensitive_data(value)
            log_entry[key] = value

        if record.exc_info and isinstance(record.exc_info, tuple) and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class LoggingManager:
    def __init__(self, app_name: str = "ai_assistant", level: str = "INFO") -> None:
        self._app_name = app_name
        self._logger = logging.getLogger(app_name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._handler = logging.StreamHandler(sys.stdout)
        self._handler.setFormatter(JSONFormatter())
        self._logger.handlers.clear()
        self._logger.addHandler(self._handler)
        self._logger.propagate = False
        self._context = LogContext()

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def set_context(self, context: LogContext) -> None:
        self._context = context

    def update_context(self, **kwargs: str) -> None:
        for key, value in kwargs.items():
            if hasattr(self._context, key) and value:
                setattr(self._context, key, value)

    def _enrich(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        enriched: dict[str, Any] = {
            "correlation_id": self._context.correlation_id or "-",
            "conversation_id": self._context.conversation_id or "-",
            "request_id": self._context.request_id or "-",
            "workflow_id": self._context.workflow_id or "-",
            "trace_id": self._context.trace_id or "-",
            "user_id": self._context.user_id or "-",
            "tenant_id": self._context.tenant_id or "-",
            "agent_id": self._context.agent_id or "-",
            "knowledge_document_id": self._context.knowledge_document_id or "-",
        }
        if extra:
            enriched.update(extra)
        return enriched

    def debug(self, message: str, **extra: Any) -> None:
        self._logger.debug(message, extra=self._enrich(extra))

    def info(self, message: str, **extra: Any) -> None:
        self._logger.info(message, extra=self._enrich(extra))

    def warning(self, message: str, **extra: Any) -> None:
        self._logger.warning(message, extra=self._enrich(extra))

    def error(self, message: str, exc_info: bool = True, **extra: Any) -> None:
        self._logger.error(message, exc_info=exc_info, extra=self._enrich(extra))

    def critical(self, message: str, **extra: Any) -> None:
        self._logger.critical(message, extra=self._enrich(extra))

    def set_level(self, level: str) -> None:
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
