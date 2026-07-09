import os

import pytest

from security.exceptions import SecurityConfigurationError
from security.secrets_manager import SecretsManager


class TestSecretsManager:
    @pytest.fixture
    def manager(self):
        mgr = SecretsManager()
        os.environ["JWT_SECRET"] = "test-jwt-secret"
        return mgr

    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        await manager.initialize()
        assert manager.initialized

    @pytest.mark.asyncio
    async def test_initialize_missing_required(self):
        mgr = SecretsManager()
        if "JWT_SECRET" in os.environ:
            del os.environ["JWT_SECRET"]
        with pytest.raises(SecurityConfigurationError):
            await mgr.initialize()

    @pytest.mark.asyncio
    async def test_get_secret(self, manager):
        await manager.initialize()
        secret = manager.get_secret("JWT_SECRET")
        assert secret == "test-jwt-secret"

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self, manager):
        await manager.initialize()
        with pytest.raises(SecurityConfigurationError):
            manager.get_secret("NONEXISTENT")

    @pytest.mark.asyncio
    async def test_set_secret(self, manager):
        await manager.initialize()
        manager.set_secret("NEW_SECRET", "new-value")
        assert manager.get_secret("NEW_SECRET") == "new-value"

    @pytest.mark.asyncio
    async def test_rotate_secret(self, manager):
        await manager.initialize()
        manager.rotate_secret("JWT_SECRET", "new-secret-value")
        assert manager.get_secret("JWT_SECRET") == "new-secret-value"

    @pytest.mark.asyncio
    async def test_has_secret(self, manager):
        await manager.initialize()
        assert manager.has_secret("JWT_SECRET")
        assert not manager.has_secret("UNKNOWN")

    @pytest.mark.asyncio
    async def test_secret_age(self, manager):
        await manager.initialize()
        import time
        time.sleep(0.01)
        age = manager.get_secret_age("JWT_SECRET")
        assert age > 0

    @pytest.mark.asyncio
    async def test_list_secret_keys(self, manager):
        await manager.initialize()
        keys = manager.list_secret_keys()
        assert "JWT_SECRET" in keys

    @pytest.mark.asyncio
    async def test_validate_all(self, manager):
        await manager.initialize()
        results = manager.validate_all()
        assert results["JWT_SECRET"] is True

    @pytest.mark.asyncio
    async def test_shutdown(self, manager):
        await manager.initialize()
        await manager.shutdown()
        assert not manager.initialized
