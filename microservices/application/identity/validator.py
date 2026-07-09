import re

import jwt

from config.settings import settings
from exceptions.base import ValidationError


class IdentityValidator:
    def __init__(self) -> None:
        self._jwt_secret = settings.jwt_secret
        self._jwt_algorithm = settings.jwt_algorithm
        self._email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        self._phone_pattern = re.compile(r"^\+?[1-9]\d{1,14}$")

    def validate_jwt(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValidationError(message="JWT token has expired")
        except jwt.InvalidTokenError as e:
            raise ValidationError(message=f"Invalid JWT token: {e}")

    def validate_email(self, email: str) -> bool:
        return bool(self._email_pattern.match(email))

    def validate_phone(self, phone: str) -> bool:
        return bool(self._phone_pattern.match(phone))

    def validate_session_id(self, session_id: str) -> bool:
        if not session_id or len(session_id) < 8:
            return False
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", session_id))

    def validate_identity_consistency(self, existing: dict, incoming: dict) -> list[str]:
        inconsistencies: list[str] = []
        for field in ("email", "phone", "user_id"):
            if existing.get(field) and incoming.get(field) and existing[field] != incoming[field]:
                inconsistencies.append(f"{field} mismatch: {existing[field]} != {incoming[field]}")
        return inconsistencies
