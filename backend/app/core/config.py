"""Application settings, read from environment variables (.env at repo root).

See docs/prd/sambungbelajarmu-v2-prd.md T8 for the full env var list.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Minimum JWT_SECRET length (bytes/chars). Below this, HS256 signing is
# brute-forceable; refuse to start rather than run insecurely (T3).
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    JWT_SECRET: str
    JWT_ACCESS_MINUTES: int
    JWT_REFRESH_DAYS: int

    @field_validator("JWT_SECRET")
    @classmethod
    def _jwt_secret_min_length(cls, value: str) -> str:
        if len(value) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters long"
            )
        return value

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5"

    FRONTEND_ORIGIN: str


settings = Settings()
