"""Liveness endpoint.

Failure-mode contract (locked in by tests/test_health.py): this endpoint
always returns HTTP 200. The response body's "db" field reports "ok" or
"error" depending on whether `SELECT 1` succeeded, so callers can see DB
health without the liveness probe itself flapping on transient DB issues.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "ok", "db": "error"}
    return {"status": "ok", "db": "ok"}
