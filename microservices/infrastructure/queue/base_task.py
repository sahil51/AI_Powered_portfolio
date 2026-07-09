import time
import traceback
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger


class BaseTask(Task):
    abstract = True
    autoretry_for: tuple = ()
    max_retries: int = 3
    default_retry_delay: int = 60
    retry_backoff: bool = True
    retry_backoff_max: int = 600
    retry_jitter: bool = True

    _logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_task_logger(self.__class__.__module__)
        return self._logger

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        self.logger.info(
            "Task completed",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "runtime": getattr(self.request, "runtime", None),
            },
        )
        self._record_metric("success", task_id)

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        self.logger.error(
            f"Task failed: {exc}",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        self._record_metric("failure", task_id)

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        self.logger.warning(
            f"Task retry: {exc}",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "attempt": self.request.retries + 1,
                "max_retries": self.max_retries,
            },
        )
        self._record_metric("retry", task_id)

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        self.request.runtime = time.time()
        self.logger.info(
            "Task started",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )

    def after_return(self, status: str, retval: Any, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        runtime = getattr(self.request, "runtime", None)
        if runtime:
            elapsed = time.time() - runtime
            if elapsed > 30:
                self.logger.warning(
                    f"Slow task ({elapsed:.2f}s)",
                    extra={"task_name": self.name, "task_id": task_id},
                )

    def _record_metric(self, event_type: str, task_id: str) -> None:
        pass
