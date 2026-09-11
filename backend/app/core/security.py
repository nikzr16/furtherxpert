"""JWT and password-hashing primitives (PRD T3: stateless JWT login).

No DB access here on purpose -- this module only knows how to mint/verify
tokens and hash/verify passwords. Request-level wiring (turning a bearer
token into the current `User`) lives in `app/api/deps.py`.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

from app.core.config import settings

JWT_ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHash):
        return False


class InvalidTokenError(Exception):
    """Raised when a token is missing, expired, malformed, or the wrong type."""


def _create_token(user_id: uuid.UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.JWT_ACCESS_MINUTES))


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.JWT_REFRESH_DAYS))


def decode_token(token: str, expected_type: TokenType) -> dict:
    """Verify signature and expiry, then enforce the `type` claim.

    An access token must never work as a refresh token and vice versa (T3) --
    that check lives here so every caller gets it for free.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError("Invalid or expired token")

    return payload
