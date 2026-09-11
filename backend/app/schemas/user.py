"""Request/response shapes for accounts (PRD T3, T4, T6).

Field sets are locked to exactly what the PRD asks for -- no extra fields.
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import RACES

MIN_PASSWORD_LENGTH = 8
# Earliest plausible SPM year kept wide on purpose; see the model's DB CHECK
# constraint (app/models/user.py) for the equivalent wide sanity net.
_EARLIEST_SPM_YEAR = 1970


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    is_citizen: bool
    race: str
    spm_year: int
    consent: bool

    @field_validator("race")
    @classmethod
    def _race_must_be_known(cls, value: str) -> str:
        if value not in RACES:
            raise ValueError(f"race must be one of {', '.join(RACES)}")
        return value

    @field_validator("spm_year")
    @classmethod
    def _spm_year_must_be_current_ish(cls, value: int) -> int:
        current_year = datetime.now(timezone.utc).year
        if value < _EARLIEST_SPM_YEAR or value > current_year:
            raise ValueError(f"spm_year must be between {_EARLIEST_SPM_YEAR} and {current_year}")
        return value

    @field_validator("consent")
    @classmethod
    def _consent_must_be_given(cls, value: bool) -> bool:
        if not value:
            raise ValueError("consent is required to register")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    is_citizen: bool
    race: str
    spm_year: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
