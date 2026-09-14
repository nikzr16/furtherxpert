"""Tests for `eligibility.find_matching` (result explanations plan Step 10.1
task 6): one valid way the grades meet the rules, for "Why this diploma?".

Expected subjects are worked out by hand from the rule order (named-subject
rules first, "N more subjects" last) and the candidate order (best grade
first, then subject code).
"""

import random

from sqlalchemy import select

from app.models.requirement import GeneralRequirement, ProgramRequirement
from app.models.subject import Subject
from app.services.eligibility import combine_rule_trees, find_matching, tree_is_satisfiable
from app.services.scoring import GRADE_POINTS


def _subjects_by_rule(matching):
    return [[codes for _, codes in entry["parts"]] for entry in matching]


def test_counts_once_trap_has_no_matching_with_one_qualifying_subject():
    general = {"all": [{"subject": "MT", "min": "C"}]}
    program = {"all": [{"uncounted": 1, "min": "C"}]}
    assert find_matching(general, program, {"MT": "C"}) is None


def test_counts_once_trap_gives_the_specific_rule_its_subject():
    # The uncounted rule comes first, but named rules are matched first:
    # MT goes to "needs MT", so BI fills the "1 more subject" slot.
    general = {"all": [{"uncounted": 1, "min": "C"}]}
    program = {"all": [{"subject": "MT", "min": "C"}]}
    matching = find_matching(general, program, {"MT": "C", "BI": "C"})

    assert [entry["side"] for entry in matching] == ["general", "program"]
    assert _subjects_by_rule(matching) == [[["BI"]], [["MT"]]]


def test_one_of_picks_the_best_grades_then_subject_code():
    program = {"all": [{"one_of": ["FZ", "KM", "BL"], "count": 2, "min": "C"}]}
    grades = {"FZ": "B", "KM": "A", "BL": "A"}
    # A beats B; BL and KM tie on A, so code order: BL then KM.
    assert _subjects_by_rule(find_matching({"all": []}, program, grades)) == [[["BL", "KM"]]]


def test_any_uses_the_branch_that_works():
    rule = {"any": [{"subject": "MT", "min": "C"}, {"subject": "MM", "min": "C"}]}
    matching = find_matching({"all": [rule]}, {"all": []}, {"MT": "D", "MM": "B"})
    (node, codes), = matching[0]["parts"]
    assert node == {"subject": "MM", "min": "C"}
    assert codes == ["MM"]


def test_any_with_a_nested_all_returns_every_part_of_that_branch():
    rule = {
        "any": [
            {"all": [{"subject": "BI", "min": "E"}, {"one_of": ["MT", "FZ", "KM"], "count": 2, "min": "C"}]},
            {"one_of": ["BM"], "count": 1, "min": "C"},
        ]
    }
    grades = {"BI": "D", "MT": "B", "FZ": "A", "KM": "C", "BM": "D"}
    matching = find_matching({"all": []}, {"all": [rule]}, grades)
    # BM D fails the second branch, so the first: BI, then the 2 best of MT/FZ/KM.
    assert _subjects_by_rule(matching) == [[["BI"], ["FZ", "MT"]]]


def test_uncounted_takes_the_best_subjects_left_over():
    general = {"all": [{"subject": "BM", "min": "C"}, {"uncounted": 2, "min": "C"}]}
    grades = {"BM": "A+", "EK": "C", "GG": "B", "BI": "A", "SK": "B"}
    # Left after BM: BI A, GG B, SK B, EK C -> BI, then GG (code before SK).
    assert _subjects_by_rule(find_matching(general, {"all": []}, grades)) == [[["BM"]], [["BI", "GG"]]]


def test_same_matching_whatever_order_the_grades_arrive_in():
    general = {"all": [{"subject": "BM", "min": "C"}, {"subject": "SJ", "min": "E"}, {"uncounted": 2, "min": "C"}]}
    program = {"all": [{"one_of": ["FZ", "KM", "BL", "SK"], "count": 1, "min": "C"}, {"uncounted": 2, "min": "C"}]}
    items = [("BM", "A"), ("SJ", "B"), ("FZ", "B"), ("KM", "B"), ("BL", "A"), ("SK", "A"), ("EK", "B"), ("GG", "A")]
    rng = random.Random(3)
    expected = None
    for _ in range(50):
        rng.shuffle(items)
        result = _subjects_by_rule(find_matching(general, program, dict(items)))
        expected = expected or result
        assert result == expected


def _codes_in(node, found):
    for key in ("subject",):
        if key in node:
            found.add(node[key])
    for code in node.get("one_of", []):
        found.add(code)
    for child in node.get("any", []) + node.get("all", []):
        _codes_in(child, found)


def test_matching_exists_exactly_when_the_checker_passes_for_every_real_rule_tree(db_session):
    """Every real syarat khas row in the loaded snapshot, with random grade
    sets: `find_matching` must agree with the checker's own grade-tree test."""
    generals = {row.category: row.rules for row in db_session.execute(select(GeneralRequirement)).scalars()}
    requirements = list(db_session.execute(select(ProgramRequirement)).scalars())
    all_codes = [row for row in db_session.execute(select(Subject.code)).scalars()]
    assert requirements and generals

    rng = random.Random(2026)
    letters = list(GRADE_POINTS)
    passes = fails = 0
    for requirement in requirements:
        general = generals[requirement.category]
        rule_codes: set[str] = set()
        for node in general["all"] + requirement.rules.get("all", []):
            _codes_in(node, rule_codes)
        for _ in range(12):
            codes = set(rng.sample(sorted(rule_codes), k=max(1, len(rule_codes) * 2 // 3))) if rule_codes else set()
            codes |= set(rng.sample(all_codes, k=4)) | {"BM", "SJ"}
            strong = rng.random() < 0.5
            grades = {
                code: rng.choice(letters[:5]) if strong else rng.choice(letters)
                for code in sorted(codes)
            }
            combined = combine_rule_trees(general, requirement.rules)
            checker_passes = tree_is_satisfiable({"all": combined["all"]}, frozenset(grades), grades)
            assert (find_matching(general, requirement.rules, grades) is not None) == checker_passes
            passes += checker_passes
            fails += not checker_passes
    # Both outcomes were really exercised.
    assert passes > 0 and fails > 0
