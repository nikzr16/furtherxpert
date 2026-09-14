"""Request/response shapes for the interest test routes (PRD T1, T6;
rotation PRD T2).

`InterestOptionPublic` deliberately carries no `area_id` / area name: PRD T6
says the question lists must not leak which option maps to which area.
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
    """Response shape for `GET /me/interest-answers`: the saved answers for
    the student's current set, plus whether every question in it is answered
    (Phase 9: all 40)."""

    answers: list[InterestAnswerOut]
    complete: bool


class InterestTestSetOut(BaseModel):
    """Response shape for `GET /me/interest-test` and
    `POST /me/interest-test/rotate` (rotation PRD T2): the student's current
    set of questions in display order, with saved answers and progress.
    `has_finished_set` is true when an earlier finished set still feeds
    My Results."""

    set_id: int
    questions: list[InterestQuestionPublic]
    answers: list[InterestAnswerOut]
    answered: int
    total: int
    complete: bool
    has_finished_set: bool
