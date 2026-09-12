# 0008 - Interest Test Partial Save (Merge) and Completeness Gate

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

Phase 6 (client pages) needs the Interest Test page to save progress as the
student answers each question, not only once they reach the last of the 20 --
so a student can close the tab partway through and pick up where they left
off later. Two things in the existing Phase 4/5 behaviour stood in the way:

1. `PUT /me/interest-answers` was a **full replace**: every call deleted
   *all* of the student's previously-saved answers, then inserted the
   payload's rows as the whole new set (`app/services/interest_test.py`,
   `replace_answers`). A client calling this after every single question
   would have to resend every answer picked so far on each save, or lose
   earlier answers the moment it didn't.
2. `GET /me/analysis` (`app/services/analysis.py`) computed interest-area
   scores (`interest_areas`, `likely_to_love`, and any sweet spot depending
   on it) from whatever picks existed, however few. A student who had
   answered only 2 of 20 questions already saw a "real-looking" interest
   radar chart and a "likely to love" area, both computed from a data set
   that's nowhere near representative of their actual interests -- exactly
   the kind of premature, misleading signal decision `0007` already fixed
   for the 0-score case, but for the *partial, nonzero* case instead.

The product owner approved fixing both before Phase 6 client work started
(see this session's task brief): saves must merge/upsert, and interest
scoring must wait for a genuinely complete (20/20) test.

## Decision

**1. `PUT /me/interest-answers` is now a merge/upsert, not a full replace.**
`app/services/interest_test.py`'s save function (renamed `save_answers`,
was `replace_answers`) updates the student's existing answer for each
payload question in place, or inserts a new row if there wasn't one yet. A
question the payload omits keeps whatever the student answered before --
it is never deleted. This holds for both a small, partial save (e.g. one
question after each click) and a full 20-question submit: a full submit is
just an upsert that happens to cover every question, so it still behaves
like the old "replace" from the student's point of view when they truly
retake the whole test in one go.

**2. New `GET /me/interest-answers`** returns `{"answers": [...],
"complete": bool}`: the student's saved answers so far, and whether all 20
questions are answered. This is what lets the client resume a
part-finished test and show progress (e.g. "12 of 20").

**3. `GET /me/analysis` gates interest scoring on completeness.** A new
`interest_test_complete` boolean is added to the response
(`app/schemas/analysis.py`). `app/services/analysis.py` computes it as
`answered_questions >= total_questions` (all 20). Until it's `true`:
- Every entry in `interest_areas` (Chart 2) is forced to a score of `0.0`
  -- the 9 areas are still always present (unchanged from the existing
  "never omitted, even at 0%" rule), but none of them reflect the partial
  picks so far.
- `likely_to_love` is forced to `[]`.
- `sweet_spots` can therefore never include an interest-driven pick either,
  the same cascading consequence decision `0007` already established for
  the 0-score case.
- `subject_groups`, `likely_to_excel`, and every program's eligibility
  verdict are **unaffected** -- they come from saved SPM grades alone, and
  keep working exactly as before regardless of interest-test completeness.

## Reason

**Why "empty chart" means "9 areas forced to 0", not an empty list:** the
existing PRD T1 / Flow 4 behaviour already guarantees `interest_areas`
always has exactly 9 entries, even when the student has never touched the
interest test ("every one of the 9 areas is always shown, even at 0%").
Changing the shape to an empty list for "incomplete" would both contradict
that existing invariant and make the client handle two different empty
shapes (never-started vs. partial-but-incomplete) for what is, from the
student's perspective, the same "no usable signal yet" state. Forcing every
score to `0.0` keeps one consistent shape and reuses the exact same
"radar chart collapses to nothing" visual the client already has to handle
for a fresh account -- there is no meaningful difference in outcome between
"hasn't started" and "started but not finished" as far as the chart goes.

**Why merge/upsert instead of keeping full-replace and requiring all 20 on
every save:** requiring the client to resend all previously-answered
questions on every save would work, but pushes bookkeeping (remembering and
resending every prior answer) onto the client for no benefit -- the server
already has the prior answers and is the natural place to merge them. Merge
is also strictly more permissive: a client that always sends the full
current answer set (old full-replace behaviour) still works identically
under a merge, since every question it cares about is present in the
payload either way.

**Why the completeness check is "answered >= total questions" rather than a
stored flag:** the student's answer count is already the source of truth
(`interest_answers` rows), and the total question count is already the
source of truth (`interest_questions` rows) -- deriving completeness from
both on every `GET` is a single cheap `COUNT` query, needs no new column or
migration, and can never drift out of sync with the actual data the way a
cached "is_complete" flag on the user row could if a future change ever let
an answer be un-answered.

**Why this doesn't touch the golden tests' expected values:** each golden
student who calls the interest test (`amir`, `mei_ling`, `priya`, `aisyah`,
`daniel`) had their `interest_picks` fixture padded with "None of the
above" for every question they hadn't already answered, reaching all 20.
"None of the above" contributes 0 picks to any area (existing rule, PRD
T1), so every expected chart/Best Fit number in `tests/golden/expected/`
is numerically unchanged -- only the new `interest_test_complete: true`
field was added. `rahman` (who never calls the interest test at all) stays
incomplete, unchanged from before. This means the golden fixtures are still
representative of a real, complete interest test under this rule, rather
than needing a parallel "deliberately partial" fixture invented just to
demonstrate the gate (that gate is instead covered directly by new tests in
`tests/test_analysis.py` and `tests/test_student_input.py`).

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 3 step 3 now
      describes the merge/upsert save and the new `GET /me/interest-answers`;
      Flow 4 step 1g/h now states the completeness gate; the Error States and
      Behavioral Constraints sections are updated to match)
- [x] Reference doc updated (`docs/reference/folder-structure.md`: routes
      table, `app/api/me.py` / `app/services/interest_test.py` /
      `app/schemas/interest_test.py` / `app/schemas/analysis.py` row
      descriptions)
- [x] Skill file unaffected: `.claude/skills/proj-furtherxpert-rules/SKILL.md`
      Section 2's interest-area scoring formula itself hasn't changed, only
      *when* it's allowed to run -- no update needed there
