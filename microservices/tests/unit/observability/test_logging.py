import io
import json
import logging

import pytest

from observability.logging_manager import LoggingManager, mask_sensitive_data


class TestLoggingManager:
    @pytest.fixture
    def manager(self):
        mgr = LoggingManager(app_name="test", level="DEBUG")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(mgr._handler.formatter)
        mgr._logger.handlers.clear()
        mgr._logger.addHandler(handler)
        mgr._stream = stream
        return mgr

    def _get_output(self, manager):
        return json.loads(manager._stream.getvalue().strip())

    def test_initialization(self, manager):
        assert manager._app_name == "test"
        assert manager._logger.level == logging.DEBUG

    def test_log_levels(self, manager):
        manager.debug("debug msg")
        manager.info("info msg")
        manager.warning("warning msg")
        manager.error("error msg")
        manager.critical("critical msg")
        output = manager._stream.getvalue()
        assert "debug msg" in output
        assert "info msg" in output

    def test_set_level(self, manager):
        manager.set_level("WARNING")
        assert manager._logger.level == logging.WARNING

    def test_context_enrichment(self, manager):
        manager.update_context(user_id="user-1", tenant_id="tenant-1")
        manager.info("test msg")
        log_data = self._get_output(manager)
        assert log_data["user_id"] == "user-1"
        assert log_data["tenant_id"] == "tenant-1"

    def test_json_output_format(self, manager):
        manager.info("hello")
        log_data = self._get_output(manager)
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "hello"
        assert log_data["logger"] == "test"

    def test_sensitive_data_masking(self):
        assert "***" in mask_sensitive_data("api_key=sk-1234567890abcdef")
        assert "***" in mask_sensitive_data("Authorization Bearer token123")
        assert mask_sensitive_data("safe data") == "safe data"

    def test_error_logging_includes_exception(self, manager):
        try:
            raise ValueError("test error")
        except ValueError:
            manager.error("error occurred")
        log_data = self._get_output(manager)
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]

    def test_correlation_id_default(self, manager):
        manager.info("msg")
        log_data = self._get_output(manager)
        assert "correlation_id" in log_data
        assert log_data["correlation_id"] == "-"

    def test_extra_fields_in_log(self, manager):
        manager.info("test msg", custom_field="custom_value")
        log_data = self._get_output(manager)
        assert log_data["custom_field"] == "custom_value"
