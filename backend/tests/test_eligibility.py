"""Unit tests for `app/services/eligibility.py` (PRD T2; skill
`proj-furtherxpert-rules` S3).

All pure: plain dict/literal inputs, no DB, no `client`/`db_session`
fixtures (see `tests/conftest.py` -- those fixtures are only for the
DB-backed tests elsewhere in this suite).
"""

from app.services.eligibility import (
    combine_rule_trees,
    evaluate_eligibility,
    grade_meets,
)


# --- grade_meets --------------------------------------------------------------


def test_grade_meets():
    assert grade_meets("A+", "C") is True
    assert grade_meets("C", "C") is True
    assert grade_meets("D", "C") is False


# --- verdict order --------------------------------------------------------------


def test_non_citizen_is_not_eligible_even_with_perfect_grades():
    general_rules = {"all": []}
    program_rules = {"all": []}
    grades = {"MT": "A+", "BM": "A+", "SJ": "A+"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=False, is_bumiputera=True)

    assert result["verdict"] == "Not Eligible"
    assert "Not a Malaysian citizen" in result["reasons"]


def test_bumiputera_only_blocks_non_bumiputera_before_grade_reasons():
    # The student is ALSO missing BM (would fail the grade tree too), but
    # the Bumiputera hard stop must fire first and be the only reason
    # reported -- no grade reasons should leak through (PRD T2, skill S3
    # point 3: Bumiputera check comes before the grade tree check).
    general_rules = {"all": [{"subject": "BM", "min": "C"}]}
    program_rules = {"all": [], "bumiputera_only": True}
    grades: dict[str, str] = {}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=False)

    assert result["verdict"] == "Not Eligible"
    assert result["reasons"] == ["This program is limited to Bumiputera students"]


# --- counts-once trap (skill S3 point 2) -----------------------------------------


def test_counts_once_trap_fails_when_only_one_qualifying_subject_exists():
    # A single "Matematik C" cannot satisfy both a specific "C in
    # Matematik" clause AND a separate uncounted-subject slot -- there is
    # only one qualifying subject on file.
    combined_all = [
        {"subject": "MT", "min": "C"},
        {"uncounted": 1, "min": "C"},
    ]
    general_rules = {"all": combined_all[:1]}
    program_rules = {"all": combined_all[1:]}
    grades = {"MT": "C"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Not Eligible"


def test_counts_once_trap_backtracking_succeeds_where_greedy_first_fit_would_fail():
    # Two C-or-better subjects on file: MT and BI. `grades` is built with MT
    # first (the natural/insertion iteration order), so a naive greedy
    # checker that resolves clauses in order and always grabs the FIRST
    # available qualifying subject for an "uncounted" slot would grab MT
    # for the uncounted clause (since it's processed first below and MT is
    # the first qualifying subject it sees) -- leaving nothing for the
    # later clause that specifically needs MT, and wrongly reporting
    # failure. Backtracking instead finds the only correct assignment:
    # uncounted <- BI, subject:MT <- MT.
    combined_all = [
        {"uncounted": 1, "min": "C"},
        {"subject": "MT", "min": "C"},
    ]
    general_rules = {"all": combined_all[:1]}
    program_rules = {"all": combined_all[1:]}
    grades = {"MT": "C", "BI": "C"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Eligible"
    assert result["reasons"] == []


# --- any (ATAU) node --------------------------------------------------------------


def test_any_node_fails_when_neither_branch_qualifies():
    general_rules = {"all": [{"any": [{"subject": "MT", "min": "C"}, {"subject": "MM", "min": "C"}]}]}
    program_rules = {"all": []}
    grades: dict[str, str] = {}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Not Eligible"


def test_any_node_passes_and_then_the_used_subject_is_unavailable_later():
    # The student has exactly one qualifying subject (MT). The `any` clause
    # can be satisfied by it -- but a SEPARATE later clause in the combined
    # tree also specifically needs MT. Since each subject counts once
    # across the whole combined tree (syarat am + syarat khas together),
    # that second clause can no longer use MT, so the overall tree fails.
    # This proves the "used once" constraint crosses the any/all boundary.
    general_rules = {"all": [{"any": [{"subject": "MT", "min": "C"}, {"subject": "MM", "min": "C"}]}]}
    program_rules = {"all": [{"subject": "MT", "min": "C"}]}
    grades = {"MT": "C"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Not Eligible"

    # Sanity check: the `any` clause alone (without the competing clause)
    # DOES pass with the same single subject.
    only_any_result = evaluate_eligibility(
        grades, general_rules, {"all": []}, is_citizen=True, is_bumiputera=True
    )
    assert only_any_result["verdict"] == "Eligible"


# --- Conditional: interview / unverifiable -----------------------------------------


def test_interview_flag_alone_is_conditional_when_grades_pass():
    general_rules = {"all": [{"subject": "BM", "min": "C"}]}
    program_rules = {"all": [], "interview": True}
    grades = {"BM": "C"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Conditional"
    assert result["reasons"] == ["Requires interview/test"]


def test_unverifiable_notes_alone_are_conditional_with_one_reason_each():
    general_rules = {"all": []}
    program_rules = {"all": [], "unverifiable": ["Bebas daripada buta warna", "Had umur tidak melebihi 18 tahun"]}
    grades: dict[str, str] = {}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Conditional"
    assert result["reasons"] == [
        "Cannot verify automatically: Bebas daripada buta warna",
        "Cannot verify automatically: Had umur tidak melebihi 18 tahun",
    ]


# --- Eligible ------------------------------------------------------------------------


def test_fully_eligible_case():
    general_rules = {"all": [{"subject": "BM", "min": "C"}, {"subject": "SJ", "min": "E"}]}
    program_rules = {"all": [{"one_of": ["MT", "FIZ", "KIM"], "min": "C"}]}
    grades = {"BM": "C", "SJ": "E", "MT": "B"}

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=False)

    assert result == {"verdict": "Eligible", "reasons": []}


# --- reasons wording -------------------------------------------------------------------


def test_grade_tree_failure_reasons_distinguish_missing_vs_too_low():
    general_rules = {"all": [{"subject": "BM", "min": "C"}, {"subject": "SJ", "min": "E"}]}
    program_rules = {"all": []}
    grades = {"BM": "D"}  # BM too low, SJ missing entirely

    result = evaluate_eligibility(grades, general_rules, program_rules, is_citizen=True, is_bumiputera=True)

    assert result["verdict"] == "Not Eligible"
    assert "Needs C in BM — you have D" in result["reasons"]
    assert "Needs E in SJ — you don't have this subject" in result["reasons"]


# --- combine_rule_trees -----------------------------------------------------------------


def test_combine_rule_trees_bumiputera_only_is_or_semantics():
    general_rules = {"all": []}  # bumiputera_only unset
    program_rules = {"all": [], "bumiputera_only": True}

    combined = combine_rule_trees(general_rules, program_rules)

    assert combined["bumiputera_only"] is True


def test_combine_rule_trees_merges_all_and_both_sides_affect_outcome():
    general_rules = {"all": [{"subject": "BM", "min": "C"}]}
    program_rules = {"all": [{"subject": "MT", "min": "C"}]}

    combined = combine_rule_trees(general_rules, program_rules)
    assert combined["all"] == [{"subject": "BM", "min": "C"}, {"subject": "MT", "min": "C"}]

    # Passing only the general side's clause is not enough...
    missing_program_side = evaluate_eligibility(
        {"BM": "C"}, general_rules, program_rules, is_citizen=True, is_bumiputera=True
    )
    assert missing_program_side["verdict"] == "Not Eligible"

    # ...and passing only the program side's clause is not enough either...
    missing_general_side = evaluate_eligibility(
        {"MT": "C"}, general_rules, program_rules, is_citizen=True, is_bumiputera=True
    )
    assert missing_general_side["verdict"] == "Not Eligible"

    # ...but both together satisfy the combined tree.
    both_sides = evaluate_eligibility(
        {"BM": "C", "MT": "C"}, general_rules, program_rules, is_citizen=True, is_bumiputera=True
    )
    assert both_sides["verdict"] == "Eligible"
