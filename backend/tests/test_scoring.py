"""Unit tests for `app/services/scoring.py` (PRD T1; skill
`proj-furtherxpert-rules` S2).

All pure: plain dict/literal inputs, no DB, no `client`/`db_session`
fixtures (see `tests/conftest.py` -- those fixtures are only for the
DB-backed tests elsewhere in this suite).
"""

import pytest

from app.services.scoring import (
    GRADE_POINTS,
    excel_scores,
    grade_percent,
    interest_area_scores,
    select_best_fit,
    subject_group_scores,
    sweet_spots,
    top_three,
)


# --- GRADE_POINTS / grade_percent -------------------------------------------


def test_grade_points_matches_prd():
    assert GRADE_POINTS == {
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


def test_grade_percent_full_precision():
    assert grade_percent("A+") == 100.0
    assert grade_percent("B") == pytest.approx(5 / 9 * 100)
    assert grade_percent("G") == 0.0


@pytest.mark.parametrize("bad_grade", ["B-", "C-", "F", ""])
def test_grade_percent_rejects_invalid_grades(bad_grade):
    with pytest.raises(ValueError):
        grade_percent(bad_grade)


# --- subject_group_scores ----------------------------------------------------


def test_subject_group_scores_omits_untaken_group():
    subject_group_of = {
        "BM": "LANGUAGES",
        "MT": "MATHEMATICS",
        "FIZ": "SCIENCES",
        "KIM": "SCIENCES",
    }
    grades = {"BM": "A", "MT": "B"}

    result = subject_group_scores(grades, subject_group_of)

    assert "LANGUAGES" in result
    assert "MATHEMATICS" in result
    assert "SCIENCES" not in result  # not falsy/0 -- the key is absent entirely


def test_subject_group_scores_averages_multiple_subjects_in_a_group():
    subject_group_of = {"FIZ": "SCIENCES", "KIM": "SCIENCES"}
    grades = {"FIZ": "A+", "KIM": "C"}  # points 9 and 3 -> mean points 6 -> 6/9*100

    result = subject_group_scores(grades, subject_group_of)

    assert result == {"SCIENCES": pytest.approx(6 / 9 * 100)}


# --- interest_area_scores -----------------------------------------------------


def test_interest_area_scores_normalises_by_max_picks():
    # "None of the above" contributes 0 picks to any area -- it simply never
    # appears as a key in picks_by_area, so areas it doesn't tag stay at
    # whatever their other picks give them (here, HEALTH gets nothing).
    picks_by_area = {"TECH": 3}
    max_picks_by_area = {"TECH": 6, "HEALTH": 4}

    result = interest_area_scores(picks_by_area, max_picks_by_area)

    assert result == {"TECH": 50.0, "HEALTH": 0.0}
    assert "HEALTH" in result  # areas are never omitted here, only in excel_scores


def test_interest_area_scores_zero_max_picks_is_zero_not_a_crash():
    result = interest_area_scores({}, {"EMPTY_AREA": 0})
    assert result == {"EMPTY_AREA": 0.0}


# --- excel_scores --------------------------------------------------------------


def test_excel_scores_omits_area_with_no_relevant_group():
    group_scores = {"MATHEMATICS": 80.0, "SCIENCES": 90.0}
    area_subject_groups = {
        "SCIENCE_TECH": ["MATHEMATICS", "SCIENCES"],
        "ARTS_DESIGN": ["ARTS"],  # student has no ARTS group score at all
    }

    result = excel_scores(group_scores, area_subject_groups)

    assert result == {"SCIENCE_TECH": pytest.approx(85.0)}
    assert "ARTS_DESIGN" not in result


# --- top_three -----------------------------------------------------------------


def test_top_three_tiebreak_then_name():
    scores = {"A_AREA": 80.0, "B_AREA": 80.0, "C_AREA": 80.0, "D_AREA": 10.0}
    tiebreak_scores = {"A_AREA": 50.0, "B_AREA": 50.0, "C_AREA": 90.0}

    result = top_three(scores, tiebreak_scores)

    # C_AREA wins the tie on tiebreak (90 > 50); A_AREA and B_AREA are then
    # tied on both score and tiebreak, so they fall back to name ascending.
    assert result == [("C_AREA", 80.0), ("A_AREA", 80.0), ("B_AREA", 80.0)]


def test_top_three_returns_fewer_than_three_when_input_is_smaller():
    result = top_three({"ONLY_ONE": 42.0})
    assert result == [("ONLY_ONE", 42.0)]


def test_top_three_does_not_mutate_inputs():
    scores = {"A": 1.0, "B": 2.0}
    tiebreak = {"A": 1.0}
    top_three(scores, tiebreak)
    assert scores == {"A": 1.0, "B": 2.0}
    assert tiebreak == {"A": 1.0}


def test_top_three_exclude_zero_false_by_default_keeps_zero_entries():
    # Default behaviour (used by "Likely to excel") must be unaffected: a
    # 0-score entry still competes for a top-3 slot like any other score.
    scores = {"A_AREA": 50.0, "B_AREA": 0.0}
    result = top_three(scores)
    assert result == [("A_AREA", 50.0), ("B_AREA", 0.0)]


def test_top_three_exclude_zero_true_drops_zero_entries():
    # "Likely to love" behaviour: 0-score entries are filtered out before
    # ranking, so they never occupy a top-3 slot even as filler.
    scores = {"A_AREA": 50.0, "B_AREA": 0.0, "C_AREA": 0.0}
    result = top_three(scores, exclude_zero=True)
    assert result == [("A_AREA", 50.0)]


def test_top_three_exclude_zero_can_return_fewer_than_three():
    scores = {"A_AREA": 0.0, "B_AREA": 0.0, "C_AREA": 0.0}
    result = top_three(scores, exclude_zero=True)
    assert result == []


def test_top_three_exclude_zero_does_not_mutate_inputs():
    scores = {"A": 0.0, "B": 2.0}
    tiebreak = {"A": 1.0}
    top_three(scores, tiebreak, exclude_zero=True)
    assert scores == {"A": 0.0, "B": 2.0}
    assert tiebreak == {"A": 1.0}


# --- sweet_spots -----------------------------------------------------------------


def test_love_top3_and_sweet_spots_exclude_zero_score_area_even_if_tied_for_excel():
    # AREA_Z is in the excel top-3 and, under the OLD rule (no exclude_zero),
    # its 0.0 love score would still have made the love top-3 as tiebreak
    # filler -- making it a sweet spot even though the student has zero
    # interest in it. The new rule (exclude_zero=True on the love call)
    # must drop it from love, and therefore from sweet_spots too, even
    # though it's still #3 in likely_to_excel.
    excel_scores = {"AREA_X": 90.0, "AREA_Y": 80.0, "AREA_Z": 70.0}
    love_scores = {"AREA_X": 60.0, "AREA_Y": 0.0, "AREA_Z": 0.0}

    # Sanity check: confirm this really was the old-rule trap.
    old_love_top3 = top_three(love_scores, tiebreak_scores=excel_scores)
    assert ("AREA_Z", 0.0) in old_love_top3

    excel_top3 = top_three(excel_scores, tiebreak_scores=love_scores)
    love_top3 = top_three(love_scores, tiebreak_scores=excel_scores, exclude_zero=True)
    sweet = sweet_spots(excel_top3, love_top3)

    assert love_top3 == [("AREA_X", 60.0)]
    assert "AREA_Z" not in sweet
    assert sweet == ["AREA_X"]


def test_sweet_spots_returns_areas_in_both_lists():
    excel_top3 = [("SCIENCE_TECH", 90.0), ("ARTS_DESIGN", 70.0), ("HEALTH", 60.0)]
    love_top3 = [("HEALTH", 95.0), ("SCIENCE_TECH", 80.0), ("MEDIA", 40.0)]

    result = sweet_spots(excel_top3, love_top3)

    assert set(result) == {"SCIENCE_TECH", "HEALTH"}
    assert result == ["SCIENCE_TECH", "HEALTH"]  # follows excel_top3's order


# --- select_best_fit ---------------------------------------------------------------


def test_select_best_fit_orders_eligible_first_then_conditional_then_name():
    programs = [
        {"name": "Zed Program", "verdict": "Eligible"},
        {"name": "Alpha Program", "verdict": "Conditional"},
        {"name": "Beta Program", "verdict": "Not Eligible"},
        {"name": "Alpha Eligible", "verdict": "Eligible"},
    ]

    result = select_best_fit(programs, limit=3)

    assert [p["name"] for p in result] == ["Alpha Eligible", "Zed Program", "Alpha Program"]


def test_select_best_fit_respects_limit():
    programs = [{"name": f"P{i}", "verdict": "Eligible"} for i in range(5)]
    result = select_best_fit(programs, limit=3)
    assert len(result) == 3
