"""Account business rules: register and authenticate (PRD T3, T4).

Pure-ish service functions on top of a `Session` -- the API layer
(`app/api/auth.py`, `app/api/me.py`) only translates HTTP <-> these calls.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import RegisterRequest


class EmailAlreadyRegisteredError(Exception):
    """Raised when the (lower-cased) email is already in use."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, payload: RegisterRequest) -> User:
    email = normalize_email(payload.email)

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        is_citizen=payload.is_citizen,
        race=payload.race,
        spm_year=payload.spm_year,
        consent_at=datetime.now(timezone.utc),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError(email) from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if the credentials match, else None.

    Always runs a hash verification even when the email is unknown (against
    a fixed dummy hash) so the response time doesn't leak whether the email
    exists, and the caller returns one generic error either way.
    """
    user = db.execute(select(User).where(User.email == normalize_email(email))).scalar_one_or_none()
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# A real argon2 hash of an unguessable, unused value -- only used so
# authenticate_user() always pays the same argon2 cost for unknown emails.
_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$w3S0cLhWdzJij6dAToG6rQ$uOAzYjoGIXi/waaLMat9WBVFgXZ05qyN4/pUxgL5Z60"
