"""`GET /me/analysis` orchestration (PRD T1, T2, T5; skill
`proj-furtherxpert-rules` S2, S3): loads a student's saved grades/answers and
the current session's reference data, calls the pure `scoring.py` /
`eligibility.py` functions, builds Best Fit, and caches the result in
`analysis` (PRD T5).

Unlike `scoring.py` / `eligibility.py`, this module is deliberately **not
pure** -- it is the one place in Phase 5 that touches the DB and the clock.
Cache invalidation is not this module's job: `app/services/results.py`
(`upsert_results`) and `app/services/interest_test.py` (`save_answers`)
delete a user's `analysis` row whenever their saved SPM results or interest
answers change, so the next call here recomputes instead of serving stale
data.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.importer.reference_data import match_interest_area
from app.models.analysis import Analysis
from app.models.interest_area import InterestArea
from app.models.interest_test import InterestAnswer, InterestOption, InterestQuestion
from app.models.program import Program
from app.models.requirement import GeneralRequirement, ProgramRequirement
from app.models.spm_result import SPMResult
from app.models.subject import Subject, SubjectGroup
from app.models.university import University
from app.models.user import User
from app.services.eligibility import evaluate_eligibility
from app.services.reference import _current_session
from app.services.scoring import (
    excel_scores,
    interest_area_scores,
    select_best_fit,
    subject_group_scores,
    sweet_spots,
    top_three,
)

# Bumiputera races (PRD T4, Domain Rule 8; mirrors app/models/user.py RACES).
BUMIPUTERA_RACES = {"Melayu", "Anak Negeri Sabah", "Anak Negeri Sarawak", "Orang Asli"}


class MissingGeneralRequirementsError(Exception):
    """Raised when no `general_requirements` row exists for the current
    session + category. Per proj-furtherxpert-rules skill Section 4, every
    loaded session must have a syarat am row for both categories -- a
    missing row is a data-integrity problem, not a normal eligibility
    outcome, so this is raised rather than silently defaulting to `{}`.
    """

    def __init__(self, session_id: int, category: str) -> None:
        self.session_id = session_id
        self.category = category
        super().__init__(f"No general_requirements row for session {session_id}, category {category!r}")


def _program_dict(program: Program, university: University, verdict_result: dict) -> dict:
    return {
        "code": program.code,
        "name": program.name,
        "university": university.name,
        "verdict": verdict_result["verdict"],
        "reasons": verdict_result["reasons"],
    }


def get_analysis(db: DbSession, user: User) -> dict:
    """Return the cached `analysis` row's result, or compute, cache, and
    return a fresh one if none exists yet (PRD T5, T6).
    """
    cached = db.execute(select(Analysis).where(Analysis.user_id == user.id)).scalar_one_or_none()
    if cached is not None:
        return cached.result

    # --- a. Grades: subject_code -> grade the student has -------------------------------
    grade_rows = db.execute(
        select(SPMResult, Subject)
        .join(Subject, SPMResult.subject_id == Subject.id)
        .where(SPMResult.user_id == user.id)
    ).all()
    grades = {subject.code: result.grade for result, subject in grade_rows}

    # --- b. Subject group map: subject_code -> group_code (global, not session-scoped) --
    subject_group_rows = db.execute(
        select(Subject.code, SubjectGroup.code).join(SubjectGroup, Subject.group_id == SubjectGroup.id)
    ).all()
    subject_group_of = dict(subject_group_rows)
    group_name_of = {g.code: g.name for g in db.execute(select(SubjectGroup)).scalars()}

    # --- c/d. Current session, category (PRD T2) -----------------------------------------
    session = _current_session(db)
    category = "A" if user.spm_year == session.latest_spm_year else "B"

    # --- e. Interest areas: area name -> subject groups used for "excel" ------------------
    areas = list(db.execute(select(InterestArea).order_by(InterestArea.id)).scalars())
    area_subject_groups = {a.name: a.subject_groups for a in areas}
    area_name_by_id = {a.id: a.name for a in areas}

    # --- f. Max picks per area: COUNT(DISTINCT question_id) per area_id -------------------
    max_picks_by_area = {a.name: 0 for a in areas}
    max_picks_rows = db.execute(
        select(InterestOption.area_id, func.count(func.distinct(InterestOption.question_id)))
        .where(InterestOption.area_id.isnot(None))
        .group_by(InterestOption.area_id)
    ).all()
    for area_id, count in max_picks_rows:
        if area_id in area_name_by_id:
            max_picks_by_area[area_name_by_id[area_id]] = count

    # --- g. Student's picks per area (skip "None of the above", area_id IS NULL) ----------
    pick_rows = db.execute(
        select(InterestOption.area_id, func.count())
        .select_from(InterestAnswer)
        .join(InterestOption, InterestAnswer.chosen_option_id == InterestOption.id)
        .where(InterestAnswer.user_id == user.id, InterestOption.area_id.isnot(None))
        .group_by(InterestOption.area_id)
    ).all()
    picks_by_area = {area_name_by_id[area_id]: count for area_id, count in pick_rows if area_id in area_name_by_id}

    # --- g2. Interest-test completeness gate (decision 0008): interest scores are only
    # computed once all 20 questions are answered -- a part-finished test must never
    # leak a partial (and therefore misleading) score into the chart or Best Fit.
    total_questions = db.execute(select(func.count()).select_from(InterestQuestion)).scalar_one()
    answered_questions = db.execute(
        select(func.count(func.distinct(InterestAnswer.question_id))).where(InterestAnswer.user_id == user.id)
    ).scalar_one()
    interest_test_complete = total_questions > 0 and answered_questions >= total_questions

    # --- h. General requirements (syarat am) for this session + category ------------------
    general = db.execute(
        select(GeneralRequirement).where(
            GeneralRequirement.session_id == session.id, GeneralRequirement.category == category
        )
    ).scalar_one_or_none()
    if general is None:
        raise MissingGeneralRequirementsError(session.id, category)

    # --- i. Programs + their requirements for this category, with eligibility -------------
    is_bumiputera = user.race in BUMIPUTERA_RACES
    program_rows = db.execute(
        select(Program, ProgramRequirement, University)
        .join(ProgramRequirement, ProgramRequirement.program_id == Program.id)
        .join(University, Program.university_id == University.id)
        .where(Program.session_id == session.id, ProgramRequirement.category == category)
    ).all()

    programs_by_area: dict[str, list[dict]] = {}
    for program, requirement, university in program_rows:
        area = match_interest_area(program.nec_code)
        if area is None:
            continue
        verdict_result = evaluate_eligibility(
            grades, general.rules, requirement.rules, is_citizen=user.is_citizen, is_bumiputera=is_bumiputera
        )
        programs_by_area.setdefault(area, []).append(_program_dict(program, university, verdict_result))

    # --- j. Scoring (pure functions from scoring.py) ---------------------------------------
    group_scores = subject_group_scores(grades, subject_group_of)
    excel_scores_ = excel_scores(group_scores, area_subject_groups)
    if interest_test_complete:
        love_scores = interest_area_scores(picks_by_area, max_picks_by_area)
        love_top3 = top_three(love_scores, tiebreak_scores=excel_scores_, exclude_zero=True)
    else:
        # Completeness gate (decision 0008): until all 20 questions are
        # answered, every interest score is forced to 0 -- a part-finished
        # test's picks so far must never appear as a real score.
        love_scores = {a.name: 0.0 for a in areas}
        love_top3 = []
    excel_top3 = top_three(excel_scores_, tiebreak_scores=love_scores)
    sweet = sweet_spots(excel_top3, love_top3)

    # --- k. Best Fit: union of excel-top3 and love-top3 areas (judgment call -- see report)
    best_fit_area_names: list[str] = []
    seen_areas: set[str] = set()
    for name, _ in excel_top3 + love_top3:
        if name not in seen_areas:
            seen_areas.add(name)
            best_fit_area_names.append(name)

    best_fit = [
        {
            "area": area_name,
            "programs": select_best_fit(programs_by_area.get(area_name, []), limit=3),
        }
        for area_name in best_fit_area_names
    ]

    # --- l/m. Round at the API edge, cache, return -----------------------------------------
    computed_at = datetime.now(timezone.utc)
    result = {
        "subject_groups": [
            {"group": code, "name": group_name_of[code], "score": round(score, 1)}
            for code, score in sorted(group_scores.items())
        ],
        "interest_areas": [{"area": a.name, "score": round(love_scores[a.name], 1)} for a in areas],
        "likely_to_excel": [{"area": name, "score": round(score, 1)} for name, score in excel_top3],
        "likely_to_love": [{"area": name, "score": round(score, 1)} for name, score in love_top3],
        "sweet_spots": sweet,
        "best_fit": best_fit,
        "category": category,
        "computed_at": computed_at.isoformat(),
        "interest_test_complete": interest_test_complete,
    }

    db.add(Analysis(user_id=user.id, result=result, computed_at=computed_at))
    db.commit()

    return result
