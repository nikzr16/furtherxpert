"""Application settings, read from environment variables (.env at repo root).

See docs/prd/sambungbelajarmu-v2-prd.md T8 for the full env var list.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    JWT_SECRET: str
    JWT_ACCESS_MINUTES: int
    JWT_REFRESH_DAYS: int

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5"

    FRONTEND_ORIGIN: str


settings = Settings()
