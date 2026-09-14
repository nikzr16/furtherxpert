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
from app.models.interest_test import InterestAnswer, InterestOption, InterestTestSet, InterestTestSetQuestion
from app.models.program import Program
from app.models.requirement import GeneralRequirement, ProgramRequirement
from app.models.spm_result import SPMResult
from app.models.subject import Subject, SubjectGroup
from app.models.university import University
from app.models.user import User
from app.services import ai_summary
from app.services.eligibility import evaluate_eligibility, find_matching
from app.services.explanations import explain_program
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


def _program_dict(program: Program, university: University, verdict_result: dict, program_rules: dict) -> dict:
    # `nec_code`, `nec_name` and `program_rules` are internal: they feed the
    # "Why this diploma?" explanation and are not returned on their own.
    return {
        "code": program.code,
        "name": program.name,
        "university": university.name,
        "verdict": verdict_result["verdict"],
        "reasons": verdict_result["reasons"],
        "nec_code": program.nec_code,
        "nec_name": program.nec_name,
        "program_rules": program_rules,
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

    # --- f. The latest finished interest test set (rotation PRD T1). A part-finished set
    # never feeds the chart (decision 0008), so without a finished set every interest
    # score stays at 0.
    finished_set_id = db.execute(
        select(InterestTestSet.id)
        .where(InterestTestSet.user_id == user.id, InterestTestSet.completed_at.isnot(None))
        .order_by(InterestTestSet.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    interest_test_complete = finished_set_id is not None

    max_picks_by_area = {a.name: 0 for a in areas}
    picks_by_area: dict[str, int] = {}
    if interest_test_complete:
        # --- f2. Max picks per area: how many questions IN THAT SET offer the area -----
        max_picks_rows = db.execute(
            select(InterestOption.area_id, func.count(func.distinct(InterestOption.question_id)))
            .join(InterestTestSetQuestion, InterestTestSetQuestion.question_id == InterestOption.question_id)
            .where(InterestTestSetQuestion.set_id == finished_set_id, InterestOption.area_id.isnot(None))
            .group_by(InterestOption.area_id)
        ).all()
        for area_id, count in max_picks_rows:
            if area_id in area_name_by_id:
                max_picks_by_area[area_name_by_id[area_id]] = count

        # --- g. Student's picks per area in that set (skip "None of the above") --------
        pick_rows = db.execute(
            select(InterestOption.area_id, func.count())
            .select_from(InterestAnswer)
            .join(InterestOption, InterestAnswer.chosen_option_id == InterestOption.id)
            .where(InterestAnswer.set_id == finished_set_id, InterestOption.area_id.isnot(None))
            .group_by(InterestOption.area_id)
        ).all()
        picks_by_area = {area_name_by_id[area_id]: count for area_id, count in pick_rows if area_id in area_name_by_id}

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
        programs_by_area.setdefault(area, []).append(
            _program_dict(program, university, verdict_result, requirement.rules)
        )

    # --- j. Scoring (pure functions from scoring.py) ---------------------------------------
    group_scores = subject_group_scores(grades, subject_group_of)
    excel_scores_ = excel_scores(group_scores, area_subject_groups)
    if interest_test_complete:
        love_scores = interest_area_scores(picks_by_area, max_picks_by_area)
        love_top3 = top_three(love_scores, tiebreak_scores=excel_scores_, exclude_zero=True)
    else:
        # Completeness gate (decision 0008): until a set is fully answered,
        # every interest score is forced to 0 -- a part-finished test's
        # picks so far must never appear as a real score.
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

    # --- k2. "Why this diploma?" for each shown program (result explanations PRD) --------
    subject_names = dict(db.execute(select(Subject.code, Subject.name_ms)).all())
    excel_rank = {name: rank for rank, (name, _) in enumerate(excel_top3, start=1)}
    love_rank = {name: rank for rank, (name, _) in enumerate(love_top3, start=1)}

    best_fit = []
    for area_name in best_fit_area_names:
        candidates = programs_by_area.get(area_name, [])
        shown = select_best_fit(candidates, limit=3)
        total = sum(1 for p in candidates if p["verdict"] in ("Eligible", "Conditional"))
        excel_why = (
            {
                "rank": excel_rank[area_name],
                "score": excel_scores_[area_name],
                "groups": [
                    (group_name_of[code], group_scores[code])
                    for code in area_subject_groups[area_name]
                    if code in group_scores
                ],
            }
            if area_name in excel_rank
            else None
        )
        love_why = (
            {
                "rank": love_rank[area_name],
                "score": love_scores[area_name],
                "picks": picks_by_area.get(area_name, 0),
                "offered": max_picks_by_area[area_name],
            }
            if area_name in love_rank
            else None
        )
        programs = []
        for position, program in enumerate(shown, start=1):
            why = explain_program(
                program=program,
                area=area_name,
                grades=grades,
                subject_names=subject_names,
                matching=find_matching(general.rules, program["program_rules"], grades),
                bumiputera_only=bool(
                    general.rules.get("bumiputera_only") or program["program_rules"].get("bumiputera_only")
                ),
                excel=excel_why,
                love=love_why,
                position=position,
                total=total,
            )
            programs.append(
                {key: program[key] for key in ("code", "name", "university", "verdict", "reasons")} | {"why": why}
            )
        best_fit.append({"area": area_name, "programs": programs})

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


def get_analysis_summary(db: DbSession, user: User) -> dict:
    """`GET /me/analysis/summary` (Phase 7, PRD T4, T7): the AI summary of
    the student's own charts, cached alongside the charts on the same
    `analysis` row.

    Reuses `get_analysis` (AI-free, unchanged) both to gate on "enough
    data" and to read the exact area/group scores the summary is built
    from -- so this function never queries grades/answers itself, and can
    never see anything `get_analysis` wouldn't already expose to the
    student. Never raises for an AI failure: a missing/placeholder key, a
    timeout, or any other OpenAI error all become the `"unavailable"`
    state (proj-auth-security skill Section 5: "an AI call failure returns
    summary: null ... it never breaks /me/analysis"), so this route can
    never 500 because of the AI.
    """
    analysis_result = get_analysis(db, user)

    # "Not enough data" (plan Phase 7 Check): the interest test isn't
    # finished (decision 0008), or no SPM results are saved yet. An empty
    # `subject_groups` list is exactly "no SPM results saved" -- every
    # group with a taken subject would otherwise appear (see
    # `scoring.subject_group_scores`), and BM+SJ are required on every
    # save, so at least one group is always present once any results exist.
    interest_incomplete = not analysis_result["interest_test_complete"]
    no_results = not analysis_result["subject_groups"]
    if interest_incomplete or no_results:
        if interest_incomplete and no_results:
            message = "Add your SPM results and finish the interest test to get an AI summary."
        elif interest_incomplete:
            message = "Finish the interest test to get an AI summary."
        else:
            message = "Add your SPM results to get an AI summary."
        return {"status": "not_enough_data", "summary": None, "message": message}

    cached = db.execute(select(Analysis).where(Analysis.user_id == user.id)).scalar_one_or_none()
    if cached is not None and cached.summary is not None:
        return {"status": "ok", "summary": cached.summary, "message": None}

    # Privacy boundary (PRD T4, proj-auth-security skill Section 5): only
    # area/group names + scores cross into ai_summary.generate_summary --
    # never email, race, citizenship, raw grades, or program data.
    area_scores = [{"name": a["area"], "score": a["score"]} for a in analysis_result["interest_areas"]]
    group_scores = [{"name": g["name"], "score": g["score"]} for g in analysis_result["subject_groups"]]

    try:
        summary_text = ai_summary.generate_summary(area_scores, group_scores)
    except ai_summary.AISummaryError:
        return {
            "status": "unavailable",
            "summary": None,
            "message": "Summary unavailable right now. Please try again later.",
        }

    if cached is not None:
        cached.summary = summary_text
        cached.summary_computed_at = datetime.now(timezone.utc)
        db.commit()

    return {"status": "ok", "summary": summary_text, "message": None}
