"""Chart scoring: grade points, subject groups, interest areas, Best Fit
(PRD T1; skill `proj-furtherxpert-rules` S2).

Pure functions only: plain data in, plain data out. No DB session, no HTTP,
no clock, no randomness -- routers/services that load subjects, groups,
areas, and programs call these with plain dicts/lists. Percent values are
never rounded here; rounding to 1 decimal happens only at the API edge
(a later stage), so this module always returns full float precision.
"""

GRADE_POINTS: dict[str, int] = {
    "A+": 9,
    "A": 8,
    "A-": 7,
    "B+": 6,
    "B": 5,
    "C+": 4,
    "C": 3,
    "D": 2,
    "E": 1,
    "G": 0,
}


def grade_percent(grade: str) -> float:
    """points / 9 * 100, full precision -- never rounded here (PRD T1).

    Raises ValueError on an unknown grade. SPM has no B-, C-, F, or blank
    grades (PRD T1): those must be rejected as input errors, not scored.
    """
    if grade not in GRADE_POINTS:
        raise ValueError(f"Unknown SPM grade: {grade!r}")
    return GRADE_POINTS[grade] / 9 * 100


def subject_group_scores(grades: dict[str, str], subject_group_of: dict[str, str]) -> dict[str, float]:
    """Mean grade_percent of the subjects the student took, per group.

    `grades`: subject_code -> grade letter the student has.
    `subject_group_of`: subject_code -> group_code, covering every subject
    the student might have a grade for.

    A group with none of its subjects taken is omitted entirely from the
    result -- never included as 0 (PRD T1, skill S2).
    """
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for subject_code, grade in grades.items():
        group_code = subject_group_of[subject_code]
        pct = grade_percent(grade)
        sums[group_code] = sums.get(group_code, 0.0) + pct
        counts[group_code] = counts.get(group_code, 0) + 1
    return {group_code: sums[group_code] / counts[group_code] for group_code in sums}


def interest_area_scores(picks_by_area: dict[str, int], max_picks_by_area: dict[str, int]) -> dict[str, float]:
    """picks / max * 100 for every area in `max_picks_by_area` (PRD T1).

    Unlike `subject_group_scores`, an area with zero picks is NOT omitted
    here -- it is included with a score of 0.0 (only the excel side omits
    areas, per PRD T1 / skill S2). If `max_picks_by_area[area] == 0` the
    score is 0.0 to avoid a division by zero; given real seed data every
    area should have at least one taggable answer option, so this branch is
    not expected to trigger in practice -- flagged as a defensive fallback,
    not a normal case.
    """
    result: dict[str, float] = {}
    for area, max_picks in max_picks_by_area.items():
        if max_picks == 0:
            result[area] = 0.0
            continue
        picks = picks_by_area.get(area, 0)
        result[area] = picks / max_picks * 100
    return result


def excel_scores(group_scores: dict[str, float], area_subject_groups: dict[str, list[str]]) -> dict[str, float]:
    """Mean of an area's subject-group scores the student actually has.

    `group_scores`: group_code -> score (from `subject_group_scores`, so
    already omits untaken groups). `area_subject_groups`: area_name ->
    subject-group codes that area uses for "excel" (PRD T1's Area mapping
    table).

    An area is omitted entirely if the student has none of its listed
    groups (PRD T1: "Areas with none of those groups are left out").
    """
    result: dict[str, float] = {}
    for area, group_codes in area_subject_groups.items():
        relevant = [group_scores[g] for g in group_codes if g in group_scores]
        if relevant:
            result[area] = sum(relevant) / len(relevant)
    return result


def top_three(
    scores: dict[str, float],
    tiebreak_scores: dict[str, float] | None = None,
) -> list[tuple[str, float]]:
    """Top 3 (name, score) pairs, descending by score (PRD T1).

    Ties are broken by `tiebreak_scores[name]` descending when a tiebreak
    dict is given and the name is present in it, then by name ascending.
    An entry with no tiebreak value available sorts after every entry that
    has one (a judgment call: "if given/present" reads as "present beats
    absent" -- see report). Returns fewer than 3 if fewer than 3 entries
    exist. Does not mutate either input.
    """
    tiebreak_scores = tiebreak_scores or {}

    def sort_key(item: tuple[str, float]) -> tuple[float, float, str]:
        name, score = item
        tiebreak = tiebreak_scores.get(name, float("-inf"))
        return (-score, -tiebreak, name)

    ordered = sorted(scores.items(), key=sort_key)
    return ordered[:3]


def sweet_spots(excel_top3: list[tuple[str, float]], love_top3: list[tuple[str, float]]) -> list[str]:
    """Area names present in both top-3 lists (PRD T1 "Sweet spot").

    Order follows `excel_top3`'s order (the PRD names "Likely to excel"
    first when describing the sweet spot).
    """
    love_names = {name for name, _ in love_top3}
    return [name for name, _ in excel_top3 if name in love_names]


def select_best_fit(programs: list[dict], limit: int = 3) -> list[dict]:
    """Programs shown for one area's Best Fit card (PRD T1).

    Only "Eligible" or "Conditional" programs are shown (never "Not
    Eligible"); Eligible first, then by name; capped at `limit`. Each
    program dict must have at least "verdict" and "name" keys. Pure
    sort/filter over already-loaded program summaries, so it lives here
    rather than stage 2's `analysis.py` (which is the part that actually
    loads programs from the DB and is therefore not pure).
    """
    _VERDICT_ORDER = {"Eligible": 0, "Conditional": 1}
    shown = [p for p in programs if p.get("verdict") in _VERDICT_ORDER]
    ordered = sorted(shown, key=lambda p: (_VERDICT_ORDER[p["verdict"]], p["name"]))
    return ordered[:limit]
