"""Response shape for `GET /me/analysis` (PRD T1, T2, T6): the two charts
(subject groups, interest areas), Best Fit (likely to excel/love, sweet
spots, programs per area), and the UPU category used to pick program rules.

Plain `BaseModel`s, no business logic -- `app/services/analysis.py` computes
(or reads the cached) dict this validates.
"""

from pydantic import BaseModel


class SubjectGroupScore(BaseModel):
    group: str
    name: str
    score: float


class InterestAreaScore(BaseModel):
    area: str
    score: float


class BestFitProgram(BaseModel):
    code: str
    name: str
    university: str
    verdict: str
    reasons: list[str]


class BestFitArea(BaseModel):
    area: str
    programs: list[BestFitProgram]


class AnalysisOut(BaseModel):
    subject_groups: list[SubjectGroupScore]
    interest_areas: list[InterestAreaScore]
    likely_to_excel: list[InterestAreaScore]
    likely_to_love: list[InterestAreaScore]
    sweet_spots: list[str]
    best_fit: list[BestFitArea]
    category: str
    computed_at: str
