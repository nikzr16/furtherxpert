"""Test-only environment setup.

Sets required env vars (docs/prd/sambungbelajarmu-v2-prd.md T8) with dummy values before any
test module imports `app.*`, so `app.core.config.Settings()` (instantiated at
import time) succeeds without a real `.env` or a live Postgres instance.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ACCESS_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_DAYS", "7")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_MODEL", "gpt-5")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
