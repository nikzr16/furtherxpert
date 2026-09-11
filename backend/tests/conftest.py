"""Test-only environment setup.

Sets required env vars (docs/prd/sambungbelajarmu-v2-prd.md T8) with dummy values before any
test module imports `app.*`, so `app.core.config.Settings()` (instantiated at
import time) succeeds without a real `.env` or a live Postgres instance.
"""

import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
# 32+ chars: app.core.config.Settings refuses to start below the minimum
# length (see app/core/config.py, MIN_JWT_SECRET_LENGTH).
os.environ.setdefault("JWT_SECRET", "test-secret-32-characters-minimum")
os.environ.setdefault("JWT_ACCESS_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_DAYS", "7")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_MODEL", "gpt-5")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

# --- Real-Postgres fixtures, for tests that need a real DB (tests/test_auth.py) ---
#
# Trade-off (see the build report): rather than SQLite or mocked sessions,
# auth tests run against a real, separate PostgreSQL database so the actual
# constraints (unique email, race/spm_year CHECKs) and the real migration are
# exercised. Isolation is a per-test transaction + SAVEPOINT that is always
# rolled back (SQLAlchemy's documented "join a session into an external
# transaction" recipe), so tests never commit anything and can never affect
# the dev database -- each test starts from a clean, migrated `users` table.
#
# `TEST_DATABASE_URL` overrides the default; otherwise it's `DATABASE_URL`
# with the database name suffixed `_test`. A refusal check below makes sure
# this can never accidentally resolve to the real dev database.

_BASE_DATABASE_URL = os.environ["DATABASE_URL"]
_DEFAULT_TEST_DATABASE_URL = _BASE_DATABASE_URL.rsplit("/", 1)[0] + "/sambungbelajarmu_test"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", _DEFAULT_TEST_DATABASE_URL)

if not TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"):
    raise RuntimeError(
        "TEST_DATABASE_URL (or DATABASE_URL + '_test') must name a database "
        "ending in '_test' -- refusing to run DB tests against a database "
        "that isn't clearly a test database."
    )

# Tests that need the DB import `app.*` themselves; make sure the app's
# engine (a module-level singleton created at import time) points at the
# test database, never the dev one.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


def _database_reachable(url: str) -> bool:
    try:
        create_engine(url).connect().close()
        return True
    except Exception:
        return False


def _ensure_test_database_exists(base_url: str, test_url: str) -> None:
    """Create the `_test` database on first run, if it doesn't exist yet."""
    admin_engine = create_engine(base_url)
    test_db_name = test_url.rsplit("/", 1)[-1]
    with admin_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
        except ProgrammingError as exc:
            if "already exists" not in str(exc):
                raise
    admin_engine.dispose()


_DB_AVAILABLE = _database_reachable(_BASE_DATABASE_URL)

if _DB_AVAILABLE:
    _ensure_test_database_exists(_BASE_DATABASE_URL, TEST_DATABASE_URL)

    _alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    _alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(_alembic_cfg, "head")

    test_engine = create_engine(TEST_DATABASE_URL)
else:
    test_engine = None


@pytest.fixture()
def db_session():
    """A DB session bound to a rolled-back transaction: nothing persists."""
    if not _DB_AVAILABLE:
        pytest.skip(f"Postgres not reachable at {_BASE_DATABASE_URL!r}; skipping DB-backed test")

    connection = test_engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """A TestClient whose `get_db` dependency is the rolled-back session above."""
    from app.core.db import get_db
    from app.core.limiter import limiter
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    # Rate-limit state is process-global; reset it so one test's login
    # attempts never spill over into the next test's quota.
    limiter.reset()

    try:
        # https:// base_url: the refresh cookie is Secure (non-negotiable,
        # see app/api/auth.py), and a Secure cookie is only re-sent by the
        # client's cookie jar over https -- plain http://testserver would
        # silently drop it between requests.
        yield TestClient(app, base_url="https://testserver")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def make_register_payload():
    """A valid /auth/register request body, with per-call overrides."""

    def _make(**overrides) -> dict:
        payload = {
            "email": f"student-{uuid.uuid4().hex[:12]}@example.com",
            "password": "correct-horse-battery",
            "is_citizen": True,
            "race": "Melayu",
            "spm_year": 2025,
            "consent": True,
        }
        payload.update(overrides)
        return payload

    return _make
