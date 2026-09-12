# 0005 - Eligibility Matching Uses Backtracking, Not Greedy First-Fit

> **Date:** 2026-09-13 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

PRD T2's rules for one program are checked as **syarat am** (general
requirements, the same for every program in a session + category) plus
**syarat khas** (that program's own extra requirements), evaluated together
as one combined tree of clauses. PRD T2 also sets a hard constraint: "each
subject counts once across syarat am and syarat khas" -- a single subject
grade (for example one "C in Matematik") can satisfy at most one clause in
the whole combined tree, even if it could, on paper, satisfy two different
clauses at once. The PRD names the fix directly: "Use a search or matching
method, not a greedy first-fit."

A **greedy first-fit** checker would walk the clause list once, in order,
and grab the first still-available subject that qualifies for each clause
as it goes. `backend/tests/test_eligibility.py`'s
`test_counts_once_trap_backtracking_succeeds_where_greedy_first_fit_would_fail`
spells out exactly why that fails: a student has 2 qualifying subjects (MT
and BI). The combined tree has an early clause that will take *any*
qualifying subject ("uncounted: 1"), and a later clause that needs
*specifically* MT. A greedy checker resolves the early clause first and
grabs MT (since MT appears first when it looks for "any qualifying
subject"), leaving nothing for the later clause that specifically needs MT
-- so it wrongly reports the student as Not Eligible, even though giving MT
to the later clause and BI to the earlier one would satisfy both.

## Decision

`backend/app/services/eligibility.py` evaluates the combined rule tree with
**backtracking**: `_ways`/`_ways_all` thread a set of `available` (not yet
used) subjects through the whole tree, and for a clause with more than one
possible way to satisfy it (`one_of`, `uncounted`), they try every
combination -- yielding one possible "subjects remaining after this clause"
outcome per way. `_ways_all` then tries each of an `all` node's children in
order, backtracking to an earlier child's alternate combination whenever a
later child can't be satisfied from what's left.
`tree_is_satisfiable`/`evaluate_eligibility` only need to know whether at
least one way through the whole tree exists, so the search short-circuits on
the first success instead of enumerating every combination.

`test_counts_once_trap_fails_when_only_one_qualifying_subject_exists` proves
the opposite case still correctly fails: when there truly is only one
qualifying subject and two clauses both need it, no combination of
backtracking finds a way to satisfy both, so the verdict is correctly Not
Eligible.

## Reason

Backtracking is the direct fix for the greedy trap above, and it is
affordable here: a student has at most a handful of SPM subjects (in
practice well under 15), and each rule-tree clause's own subject list is
similarly small, so the total search space per program stays tiny even
though it is a full search rather than a single pass.

**Known trade-off:** the separate `_diagnose` function, which generates the
plain-English *reasons* shown for a Not Eligible verdict (for example "Needs
C in Matematik — you have D"), is deliberately **best-effort** and does
**not** re-run the same global backtracking search. It checks each clause
against the student's raw grades in isolation, ignoring which subjects other
clauses may have already claimed. This means a clause that would pass on
its own, but only fails once uniqueness is enforced globally (its subject
was claimed by a different clause), can be under-reported -- it may get no
reason at all, even though the overall verdict is Not Eligible for a real
reason. The verdict itself (`tree_is_satisfiable`) is always computed by the
full backtracking search, so **the pass/fail verdict is always correct**;
only the completeness of the listed reasons can fall short in this specific
cross-clause collision case. This was accepted rather than building a
uniqueness-aware diagnosis pass, since the PRD's acceptance check (#3, "one
SPM subject can never count for 2 rules at once") is about the verdict being
correct, not about every reason being individually exhaustive, and a fully
correct diagnosis pass would add real complexity for a case the golden
tests show is uncommon in the real UPU data.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 4 explains
      the verdict order and links here for the counts-once check)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entry
      for `backend/app/services/eligibility.py` points here)
- [ ] No upstream doc update needed
