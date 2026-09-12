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
