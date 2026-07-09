from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config.settings import settings
from security.exceptions import EncryptionError


class EncryptionService:
    def __init__(self) -> None:
        self._fernet: Fernet | None = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            key = self._derive_key(settings.jwt_secret)
            self._fernet = Fernet(key)
            self._initialized = True
        except Exception as e:
            raise EncryptionError(
                message="Failed to initialize encryption service",
                detail=str(e),
            )

    def _derive_key(self, secret: str) -> bytes:
        salt = hashlib.sha256(b"ai_assistant_encryption_salt").digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret.encode()))

    def encrypt(self, data: str) -> str:
        if not self._fernet:
            raise EncryptionError(message="Encryption service not initialized")
        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            raise EncryptionError(message="Encryption failed", detail=str(e))

    def decrypt(self, encrypted_data: str) -> str:
        if not self._fernet:
            raise EncryptionError(message="Encryption service not initialized")
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise EncryptionError(message="Decryption failed", detail=str(e))

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        pwhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return base64.b64encode(salt + pwhash).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            decoded = base64.b64decode(hashed.encode())
            salt = decoded[:16]
            pwhash = decoded[16:]
            new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
            return pwhash == new_hash
        except Exception:
            return False

    def encrypt_object(self, obj: dict[str, Any]) -> str:
        import json
        return self.encrypt(json.dumps(obj, default=str))

    def decrypt_object(self, encrypted_data: str) -> dict[str, Any]:
        import json
        return json.loads(self.decrypt(encrypted_data))

    async def shutdown(self) -> None:
        self._fernet = None
        self._initialized = False
