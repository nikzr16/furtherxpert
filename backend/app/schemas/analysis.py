"""Response shape for `GET /me/analysis` (PRD T1, T2, T6): the two charts
(subject groups, interest areas), Best Fit (likely to excel/love, sweet
spots, programs per area), and the UPU category used to pick program rules.
Also `AnalysisSummaryOut`, the response shape for `GET /me/analysis/summary`
(PRD T4, T7, Phase 7).

Plain `BaseModel`s, no business logic -- `app/services/analysis.py` computes
(or reads the cached) dict this validates.
"""

from typing import Literal

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
    # Whether the student has a fully answered 40-question set yet (decision
    # 0008). Interest scores (`interest_areas`, `likely_to_love`, and any
    # sweet spot that depends on it) are only ever computed once this is
    # `true` -- until then every `interest_areas` entry is forced to 0.0
    # and `likely_to_love` stays empty, so the client can show "finish the
    # interest test" instead of a premature/partial chart.
    interest_test_complete: bool


class AnalysisSummaryOut(BaseModel):
    """`GET /me/analysis/summary` (Phase 7, PRD T4, T7): a separate,
    allowed-to-fail call -- `GET /me/analysis` never depends on this
    succeeding.

    - `"not_enough_data"`: the interest test isn't finished yet, or no SPM
      results are saved yet. `summary` is `None`; `message` explains what's
      missing. The AI is never called for this state.
    - `"ok"`: `summary` holds the plain-English text (cached or freshly
      generated); `message` is `None`.
    - `"unavailable"`: the AI call failed (timeout, API error, or a
      missing/placeholder key). `summary` is `None`; `message` is a
      friendly, generic notice -- never the underlying error.
    """

    status: Literal["not_enough_data", "ok", "unavailable"]
    summary: str | None
    message: str | None
