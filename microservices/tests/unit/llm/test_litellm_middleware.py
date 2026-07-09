import asyncio

import pytest

from application.ai.exceptions import ProviderTimeoutError
from infrastructure.llm.lite_llm_middleware import LiteLLMMiddleware


class TestLiteLLMMiddleware:
    def setup_method(self):
        self.middleware = LiteLLMMiddleware(timeout=0.1)

    async def test_apply_timeout_success(self):
        async def fast():
            return "done"

        result = await self.middleware.apply_timeout(fast())
        assert result == "done"

    async def test_apply_timeout_raises(self):
        async def slow():
            await asyncio.sleep(5)
            return "done"

        with pytest.raises(ProviderTimeoutError):
            await self.middleware.apply_timeout(slow())

    def test_log_request_no_error(self):
        self.middleware.log_request("test-model", [{"role": "user", "content": "hi"}])

    def test_log_response_no_error(self):
        self.middleware.log_response("test-model", 100.0, True)
        self.middleware.log_response("test-model", 100.0, False)
