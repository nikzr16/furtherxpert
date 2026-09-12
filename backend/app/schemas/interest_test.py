"""Request/response shapes for `GET /interest-test` and
`PUT /me/interest-answers` (PRD T1, T6).

`InterestOptionPublic` deliberately carries no `area_id` / area name: PRD T6
says `GET /interest-test` must not leak which option maps to which area.
"""

from pydantic import BaseModel


class InterestOptionPublic(BaseModel):
    id: int
    text: str

    model_config = {"from_attributes": True}


class InterestQuestionPublic(BaseModel):
    id: int
    text: str
    options: list[InterestOptionPublic]

    model_config = {"from_attributes": True}


class InterestAnswerIn(BaseModel):
    question_id: int
    option_id: int


class InterestAnswerOut(BaseModel):
    question_id: int
    option_id: int


class InterestAnswersProgressOut(BaseModel):
    """Response shape for `GET /me/interest-answers` (Phase 6 client pages):
    the student's saved answers so far, plus whether all 20 questions have
    been answered yet. `complete` drives the completeness gate on
    `GET /me/analysis`'s interest chart/Best Fit (see
    `app/services/analysis.py`) and lets the client resume a part-finished
    test and show progress (e.g. "12 of 20")."""

    answers: list[InterestAnswerOut]
    complete: bool
