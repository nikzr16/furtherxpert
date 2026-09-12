"""UPU eligibility checker (PRD T2; skill `proj-furtherxpert-rules` S3).

Pure functions only: plain data in, plain data out. No DB session, no HTTP,
no clock, no randomness. Callers (a later stage) already pick the right
category (A/B) and load `general_requirements.rules` / `program_requirements.rules`
before calling `evaluate_eligibility`.

**Counts-once**: syarat am and syarat khas are evaluated together as one
rule tree, and each student subject may satisfy at most one clause across
the whole tree (PRD T2, skill S3 point 2 -- e.g. a single "Math C" cannot
satisfy both a `{"subject": "MT", "min": "C"}` clause AND an `{"uncounted":
1}` slot). This is solved with backtracking (`_ways`/`tree_is_satisfiable`)
rather than a greedy first-fit, which can wrongly pass or fail that trap.
Subject counts are small (<= 15), so a full backtracking search is cheap.

`evaluate_eligibility` never raises for a normal eligibility computation --
it always returns a `{"verdict": ..., "reasons": [...]}` result. The one
exception is a malformed rule-tree node (an unrecognised node shape), which
raises `ValueError` -- that is treated as corrupt reference data, not a
student-facing eligibility outcome.
"""

from itertools import combinations
from typing import Iterator

from app.services.scoring import GRADE_POINTS

_NODE_KEYS = ("subject", "one_of", "uncounted", "any", "all")


def grade_meets(actual: str, minimum: str) -> bool:
    """True if `actual` is at least as good as `minimum` (skill S3)."""
    return GRADE_POINTS[actual] >= GRADE_POINTS[minimum]


def _node_type(node: dict) -> str:
    for key in _NODE_KEYS:
        if key in node:
            return key
    raise ValueError(f"Unknown rule-tree node: {node!r}")


def _ways(node: dict, available: frozenset[str], grades: dict[str, str]) -> Iterator[frozenset[str]]:
    """Yield one `available`-minus-used-subjects frozenset per distinct way
    `node` can be satisfied, threading subject usage through the tree
    (skill S3, "required implementation approach").
    """
    node_type = _node_type(node)

    if node_type == "subject":
        subject = node["subject"]
        minimum = node["min"]
        if subject in available and grade_meets(grades[subject], minimum):
            yield available - {subject}
        return

    if node_type == "one_of":
        subjects = node["one_of"]
        minimum = node["min"]
        count = node.get("count", 1)
        qualifying = [s for s in subjects if s in available and grade_meets(grades[s], minimum)]
        for combo in combinations(qualifying, count):
            yield available - set(combo)
        return

    if node_type == "uncounted":
        minimum = node["min"]
        count = node["uncounted"]
        qualifying = [s for s in available if grade_meets(grades[s], minimum)]
        for combo in combinations(qualifying, count):
            yield available - set(combo)
        return

    if node_type == "any":
        for child in node["any"]:
            yield from _ways(child, available, grades)
        return

    if node_type == "all":
        yield from _ways_all(node["all"], available, grades)
        return

    raise ValueError(f"Unknown rule-tree node: {node!r}")  # pragma: no cover (unreachable via _node_type)


def _ways_all(children: list[dict], available: frozenset[str], grades: dict[str, str]) -> Iterator[frozenset[str]]:
    """Fold `_ways` across an `all` node's children, backtracking so a later
    child can force an earlier child to pick a different combination.
    """
    if not children:
        yield available
        return
    first, *rest = children
    for way in _ways(first, available, grades):
        yield from _ways_all(rest, way, grades)


def tree_is_satisfiable(node: dict, available: frozenset[str], grades: dict[str, str]) -> bool:
    """True if `node` can be satisfied at all from `available`.

    Only checks existence of at least one way -- does not materialize the
    whole generator (`next(iter(...), None)` short-circuits after the first
    match).
    """
    return next(iter(_ways(node, available, grades)), None) is not None


def combine_rule_trees(general_rules: dict, program_rules: dict) -> dict:
    """Merge syarat am (`general_rules`) and syarat khas (`program_rules`)
    into one combined tree/flags (PRD T2: "evaluated together").

    A missing `"all"` key is treated as `[]`, not an error.
    """
    bumiputera_only = general_rules.get("bumiputera_only", False) or program_rules.get("bumiputera_only", False)
    interview = general_rules.get("interview", False) or program_rules.get("interview", False)
    return {
        "all": general_rules.get("all", []) + program_rules.get("all", []),
        "bumiputera_only": bool(bumiputera_only),
        "interview": bool(interview),
        "unverifiable": general_rules.get("unverifiable", []) + program_rules.get("unverifiable", []),
    }


def _diagnose(node: dict, grades: dict[str, str]) -> list[str]:
    """Best-effort, per-clause reasons for why `node` fails on its own,
    IGNORING the global "each subject used once" constraint (skill S3 point
    5 example: "Needs C in Matematik -- you have D").

    Known limitation (best-effort, not over-engineered -- see report): a
    clause that only fails because of the global uniqueness constraint (it
    would pass in isolation, but its subject is claimed by another clause)
    gets no reason here. Conversely an `any` node only gets a reason when
    EVERY branch fails independently; if one branch would pass on its own,
    the whole `any` node is treated as fine here even though the overall
    tree might still fail once uniqueness is enforced globally.
    """
    node_type = _node_type(node)

    if node_type == "subject":
        subject, minimum = node["subject"], node["min"]
        if subject not in grades:
            return [f"Needs {minimum} in {subject} — you don't have this subject"]
        if not grade_meets(grades[subject], minimum):
            return [f"Needs {minimum} in {subject} — you have {grades[subject]}"]
        return []

    if node_type == "one_of":
        subjects, minimum, count = node["one_of"], node["min"], node.get("count", 1)
        qualifying = [s for s in subjects if s in grades and grade_meets(grades[s], minimum)]
        if len(qualifying) >= count:
            return []
        names = " / ".join(subjects)
        return [f"Needs {minimum} in {count} of ({names}) — you qualify for {len(qualifying)}"]

    if node_type == "uncounted":
        minimum, count = node["min"], node["uncounted"]
        qualifying = [s for s in grades if grade_meets(grades[s], minimum)]
        if len(qualifying) >= count:
            return []
        return [f"Needs {count} more subject(s) at {minimum} or better — you have {len(qualifying)}"]

    if node_type == "any":
        branch_reasons = [_diagnose(child, grades) for child in node["any"]]
        if all(branch_reasons):  # every branch produced at least one reason -> every branch failed alone
            return [reason for reasons in branch_reasons for reason in reasons]
        return []

    if node_type == "all":
        return [reason for child in node["all"] for reason in _diagnose(child, grades)]

    raise ValueError(f"Unknown rule-tree node: {node!r}")  # pragma: no cover (unreachable via _node_type)


def _dedupe(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            deduped.append(reason)
    return deduped


def evaluate_eligibility(
    grades: dict[str, str],
    general_rules: dict,
    program_rules: dict,
    is_citizen: bool,
    is_bumiputera: bool,
) -> dict:
    """PRD T2 verdict: "Eligible" | "Conditional" | "Not Eligible", with
    plain-English reasons. Verdict order (skill S3 point 3) is fixed:

    1. Not a citizen -> Not Eligible.
    2. Combined `bumiputera_only` and not Bumiputera -> Not Eligible.
    3. Combined grade tree not satisfiable -> Not Eligible.
    4. Combined `interview` or non-empty `unverifiable` -> Conditional.
    5. Otherwise -> Eligible.
    """
    if not is_citizen:
        return {"verdict": "Not Eligible", "reasons": ["Not a Malaysian citizen"]}

    combined = combine_rule_trees(general_rules, program_rules)

    if combined["bumiputera_only"] and not is_bumiputera:
        return {
            "verdict": "Not Eligible",
            "reasons": ["This program is limited to Bumiputera students"],
        }

    available = frozenset(grades.keys())
    combined_all = combined["all"]
    if not tree_is_satisfiable({"all": combined_all}, available, grades):
        reasons = []
        for child in combined_all:
            reasons.extend(_diagnose(child, grades))
        return {"verdict": "Not Eligible", "reasons": _dedupe(reasons)}

    conditional_reasons: list[str] = []
    if combined["interview"]:
        conditional_reasons.append("Requires interview/test")
    for note in combined["unverifiable"]:
        conditional_reasons.append(f"Cannot verify automatically: {note}")
    if conditional_reasons:
        return {"verdict": "Conditional", "reasons": _dedupe(conditional_reasons)}

    return {"verdict": "Eligible", "reasons": []}
