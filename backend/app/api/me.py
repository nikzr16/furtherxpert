"""The current account: read, delete, SPM results, interest-test answers
(PRD T3, T4, T6). Every handler resolves the user from the access token via
`get_current_user` (never a path/body id) and scopes its query to that user
-- proj-auth-security skill Section 3.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.interest_test import InterestAnswerIn, InterestAnswerOut
from app.schemas.spm_result import SPMResultIn, SPMResultOut
from app.schemas.user import UserPublic
from app.services import interest_test as interest_test_service
from app.services import results as results_service

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    # Deletes only the row resolved from the access token (never a
    # path/body id) -- future student tables cascade via FK ON DELETE
    # CASCADE once they exist (Phase 4+).
    db.delete(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/results", response_model=list[SPMResultOut])
def read_my_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return results_service.list_results(db, current_user.id)


@router.put("/me/results", response_model=list[SPMResultOut])
def replace_my_results(
    payload: list[SPMResultIn],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        return results_service.upsert_results(db, current_user.id, payload)
    except (
        results_service.DuplicateSubjectError,
        results_service.MissingRequiredSubjectsError,
        results_service.UnknownSubjectError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/me/interest-answers", response_model=list[InterestAnswerOut])
def replace_my_interest_answers(
    payload: list[InterestAnswerIn],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        return interest_test_service.replace_answers(db, current_user.id, payload)
    except (
        interest_test_service.DuplicateQuestionError,
        interest_test_service.UnknownQuestionError,
        interest_test_service.UnknownOptionError,
        interest_test_service.OptionQuestionMismatchError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
