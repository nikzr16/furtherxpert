# 0007 - "Likely to Love" Excludes 0-Score Interest Areas

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

`GET /me/analysis`'s "Likely to love" list (PRD T1; skill `proj-furtherxpert-rules`
S2) used `top_three` to always return exactly 3 interest areas, ranked by
interest score, regardless of whether the student actually had any interest
in those areas. Because interest score is `picks / max_picks * 100` and every
area is always present in the scored dict (never omitted, unlike the excel
side), a student with fewer than 3 areas of genuine interest still got a
full 3-item love list padded out with 0-score areas as tiebreak filler.

The product owner flagged two concrete cases where this reads as actively
misleading rather than just imprecise:
- A tech-focused student who picked only Science & Technology options
  throughout the interest test saw "Likely to love: Science & Technology
  (100), [some other area] (0), [some other area] (0)" -- presented with
  equal visual weight to three areas, two of which they have zero measured
  interest in.
- A student who never took the interest test at all (or picked "None of
  the above" on every question) saw a full 3-area "Likely to love" list
  where every entry scored 0 -- appearing to recommend areas based on
  interest data that doesn't exist.

## Decision

`app/services/scoring.py`'s `top_three` gains an `exclude_zero: bool = False`
parameter. When `True`, entries with `score == 0` are filtered out of the
input *before* ranking/limiting, so the result can hold 0 to 3 entries
instead of always exactly 3. Default is `False`, so every existing caller is
unaffected unless it opts in.

`app/services/analysis.py`'s `get_analysis` passes `exclude_zero=True` only
on the "Likely to love" call (`top_three(love_scores, tiebreak_scores=
excel_scores_, exclude_zero=True)`). The "Likely to excel" call
(`top_three(excel_scores_, tiebreak_scores=love_scores)`) is untouched and
keeps returning its top 3 exactly as before -- excel scores are never
filtered by zero, and an area with an excel score of 0 is not possible under
the existing rule anyway (an area with none of its subject groups is omitted
from `excel_scores` entirely, not scored as 0).

`sweet_spots`'s own code is unchanged -- it still just returns the area
names present in both top-3 lists it is given. But because its `love_top3`
input can no longer contain a 0-score area, a 0-score area can no longer
appear as a Sweet spot. This is a direct, intended consequence of this
decision, not a separate rule or a bug: an area the student measurably has
zero interest in should never be presented as a "sweet spot" between their
strengths and their interests, even if it happened to rank in their
excel top-3.

## Reason

**Why 0 is treated as "no signal" rather than "some interest":** the interest
score formula is `picks / max_picks * 100`; a score of exactly 0 is only
reachable by picking zero of that area's tagged options across every
question the student answered (including the degenerate case of answering
no questions, or picking "None of the above" throughout). There is no
partial-interest reading of 0 -- it unambiguously means "this student gave
no signal at all toward this area," as distinct from a low-but-nonzero score
which does represent measured, if weak, interest. That's a clean, discrete
boundary already implied by the existing formula, not a new heuristic
threshold.

**Why this doesn't need a diffing/threshold approach:** an alternative design
would pick some cutoff above 0 (e.g. "exclude scores below 10") to also hide
weak-but-nonzero interest. That was rejected: it would require inventing and
justifying an arbitrary number with no basis in the PRD, and it would start
filtering out genuine (if modest) signal, not just the "no signal" case this
decision targets. Filtering strictly at `score == 0` requires no threshold
tuning, has no edge cases to get wrong (a score is either exactly 0 or it
isn't), and directly fixes both cases the product owner raised without
touching any other behavior.

**Why the exclusion lives in `scoring.py`, not `analysis.py`:** `scoring.py`'s
module docstring commits to "pure functions only: plain data in, plain data
out." Filtering belongs inside the shared `top_three` selector (as an opt-in
parameter) rather than as ad-hoc dict-filtering bolted onto the call site in
`analysis.py`, which would duplicate ranking logic outside the one function
that owns it and risk the excel and love paths drifting apart.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 4 steps h
      and i now state the 0-score exclusion, that Likely to love can return
      0-3 areas, and that Sweet spot can no longer include a 0-score area)
- [x] Skill file updated (`.claude/skills/proj-furtherxpert-rules/SKILL.md`
      S2 "Top lists" row now states excel is unchanged and love excludes
      0-score areas)
- [x] Golden expected-value files updated (`backend/tests/golden/expected/
      {amir,mei_ling,priya,rahman,aisyah,daniel}.json` -- each file's
      `_derivation` field records the before/after love list and sweet
      spots for that student under this rule)
- [ ] No upstream doc update needed for reference data / folder structure
      (`docs/reference/folder-structure.md`) -- this is a pure logic + test
      + doc change; no files moved, added, or removed structurally
