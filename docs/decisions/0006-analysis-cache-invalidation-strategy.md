# 0006 - Analysis Cache Invalidation Is Unconditional, Not Diffed

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

`GET /me/analysis` (PRD T1, T2, T5) is expensive relative to the other `/me`
routes: it loads a student's grades and interest-test answers, the current
session's reference data, runs eligibility for every program in the
student's category, and builds Best Fit. PRD T5 asks for this to be cached
in the new `analysis` table rather than recomputed on every request.

That cache needs to go stale the moment the input data it was built from
changes -- specifically, whenever the student saves new SPM results
(`PUT /me/results`) or a new/retaken set of interest-test answers
(`PUT /me/interest-answers`). Both routes had two implementation choices for
deciding *when* to invalidate the cache: diff the incoming payload against
what's already saved and only invalidate if something actually changed, or
invalidate every time the save succeeds, regardless of whether the new data
is actually different from the old data.

## Decision

`app/services/results.py`'s `upsert_results` and
`app/services/interest_test.py`'s `replace_answers` both delete the
student's `analysis` row **unconditionally** on every successful save --
there is no comparison against the previous grades/answers first. A save
that happens to resubmit exactly the same data the student already had on
file still deletes the cache, so the very next `GET /me/analysis` recomputes
from scratch even though the recomputed result will be identical to what was
just deleted.

## Reason

**The trade-off accepted:** an identical-data resave forces one avoidable
recompute on the next `GET /me/analysis`, instead of being recognised as a
no-op and leaving the existing cache in place.

**Why this was accepted anyway:** unconditional invalidation is
correct-by-construction -- there is no way for it to have a bug that misses
a real change, because it never tries to distinguish "changed" from
"unchanged" in the first place. A diffing approach would need to compare
every subject/grade pair (for results) or every question/option pair (for
answers) correctly, including edge cases like a payload that adds one
subject while leaving nine others exactly the same, or a retake that
reorders the same answers. Any gap in that comparison logic would silently
serve a stale cached analysis to a student whose real results changed --
exactly the bug PRD T5's caching feature must not have. Given that
`PUT /me/results` and `PUT /me/interest-answers` are not called often per
student (a handful of times while filling in results, plus occasional
retakes), the cost of an occasional unnecessary recompute is small and
worth paying to remove that entire class of bug.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 4's cache
      section and Behavioral Constraints both state invalidation is
      unconditional and link here)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entries
      for `results.py`, `interest_test.py`, and the `analysis` table point
      here)
- [ ] No upstream doc update needed
