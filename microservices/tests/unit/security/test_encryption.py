import pytest

from security.encryption_service import EncryptionService
from security.exceptions import EncryptionError


class TestEncryptionService:
    @pytest.fixture
    async def service(self):
        svc = EncryptionService()
        await svc.initialize()
        return svc

    @pytest.mark.asyncio
    async def test_initialization(self):
        svc = EncryptionService()
        await svc.initialize()
        assert svc.initialized

    @pytest.mark.asyncio
    async def test_encrypt_decrypt(self, service):
        original = "sensitive data"
        encrypted = service.encrypt(original)
        assert encrypted != original
        decrypted = service.decrypt(encrypted)
        assert decrypted == original

    @pytest.mark.asyncio
    async def test_encrypt_empty(self, service):
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        assert decrypted == ""

    @pytest.mark.asyncio
    async def test_decrypt_invalid(self, service):
        with pytest.raises(EncryptionError):
            service.decrypt("invalid-data")

    @pytest.mark.asyncio
    async def test_password_hash_verify(self, service):
        password = "my_secure_password"
        hashed = service.hash_password(password)
        assert hashed != password
        assert service.verify_password(password, hashed)

    def test_password_verify_wrong(self, service):
        password = "correct"
        hashed = service.hash_password(password)
        assert not service.verify_password("wrong", hashed)

    @pytest.mark.asyncio
    async def test_encrypt_object(self, service):
        obj = {"user_id": "u-1", "role": "admin"}
        encrypted = service.encrypt_object(obj)
        decrypted = service.decrypt_object(encrypted)
        assert decrypted == obj

    @pytest.mark.asyncio
    async def test_encryption_uninitialized(self):
        svc = EncryptionService()
        with pytest.raises(EncryptionError):
            svc.encrypt("data")

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.shutdown()
        assert not service.initialized
