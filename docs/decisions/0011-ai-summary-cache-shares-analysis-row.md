# 0011 - The AI Summary Is Cached on the Existing `analysis` Row, Not a New Table

> **Date:** 2026-09-14 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

Phase 7's `GET /me/analysis/summary` (PRD T4, T7) needs its own cache, for
the same reason Phase 5's `GET /me/analysis` does (decision `0006`): calling
GPT-5 is slow and costs money per call, so a repeat request for the same,
unchanged data should be served from a saved value instead of calling the
AI again.

There were two ways to store that cached summary: a new table (for example
`analysis_summary`, keyed on `user_id`, holding `summary` and
`summary_computed_at`), or 2 new nullable columns added to the existing
`analysis` table (Phase 5, decision `0006`) that already caches the charts.

Either way, the cache needs to go stale on exactly the same trigger the
charts' cache already uses: whenever `PUT /me/results` or
`PUT /me/interest-answers` succeeds (decision `0006`). A new table would
need its own invalidation code added to those same 2 save paths, duplicating
logic that already exists for `analysis`.

## Decision

`app/models/analysis.py`'s `Analysis` model gets 2 new nullable columns,
`summary` (`Text`) and `summary_computed_at` (`DateTime`), added by
migration `96f63a9f3e5c_add_ai_summary_columns_to_analysis.py`. No new
table is created. The summary is filled in lazily: it stays `NULL` until
the first `GET /me/analysis/summary` call for that row generates one.

## Reason

**The trade-off accepted:** the `analysis` row now mixes 2 different kinds
of cached data (deterministic, code-computed charts vs. an AI-generated
summary) on one row, which is slightly less clean than one table per
concern. A future reader has to know that a `NULL` `summary` can mean
either "never asked" or "row was just created and only the charts are
filled in yet" -- there's no separate "not yet attempted" vs. "attempted and
failed" distinction stored (a failure is never cached; see decision `0012`'s
sibling reasoning in `ai_summary.py`, which raises rather than returning a
placeholder).

**Why this was accepted anyway:** because the summary always depends on
exactly the same inputs (the student's saved SPM results and interest-test
answers) as the charts, it must go stale at exactly the same moment the
charts do -- there is no scenario where the charts are stale but the
summary is still valid, or vice versa. Riding on the same row means the
existing unconditional-delete-on-save invalidation
(`app/services/results.py` / `app/services/interest_test.py`, decision
`0006`) covers the summary automatically, with zero new invalidation code:
deleting the whole `analysis` row on every successful save already deletes
`summary` and `summary_computed_at` right along with `result` and
`computed_at`. A second table would require writing and testing a second,
parallel invalidation path that has to stay perfectly in sync with the
first one forever -- exactly the kind of duplicated logic that drifts over
time. `DELETE /me`'s cascade also needed no new code for the same reason:
one `ON DELETE CASCADE` FK already covers both.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 6 section
      3 "Caching and invalidation" and the Behavioral Constraints list both
      describe this and link here)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entries
      for `models/analysis.py`, the new migration, and the `analysis` table
      row all point here)
- [ ] No upstream doc update needed
