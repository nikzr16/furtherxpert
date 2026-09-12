"""`GET /interest-test` (PRD T1, T6). Public -- like `app/api/reference.py`'s
routes, this is a lookup list, not student data. The response never exposes
which option maps to which area (see `app/schemas/interest_test.py`).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.interest_test import InterestQuestionPublic
from app.services import interest_test as interest_test_service

router = APIRouter(tags=["interest-test"])


@router.get("/interest-test", response_model=list[InterestQuestionPublic])
def read_interest_test(db: Session = Depends(get_db)) -> list:
    return interest_test_service.list_questions(db)
