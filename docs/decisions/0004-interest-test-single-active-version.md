# 0004 - Interest Test Has No Versioned Coexistence

> **Date:** 2026-09-12 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

Phase 3's UPU (public-university admission) reference data is loaded by
**session** (for example "2026/2027"), and its data migration
(`6676e66b52e5_load_2026_2027_upu_snapshot.py`) replaces only that one
session's rows when it re-runs -- other sessions, loaded in earlier years,
stay untouched and readable. Multiple sessions can exist side by side in
the database at once.

Phase 4's interest test uses `backend/data/interest_test.json`, which
carries its own `"version"` field (`"2026-09-12"`). The seed migration
(`1fa628967fac_seed_approved_interest_test.py`) had the option of copying
the session pattern -- keying its replace logic on that `version` field, so
an older approved question set could stay in the database alongside a newer
one.

## Decision

The seed migration does **not** key its replace on `version`. Re-running it
(for example after the product owner approves a revised question set)
always deletes every existing `interest_questions` and `interest_options`
row first, then reloads the file fresh. There is only ever **one** active
interest test in the database at a time -- there is no way for two versions
to coexist, and no column recording which version a given `interest_answers`
row was answered against.

## Reason

The UPU snapshot needs multi-session coexistence because a student's
eligibility depends on which admission session they're being checked
against, and the app may reasonably need to show or compare more than one
session. The interest test has no equivalent product need: PRD T1's area
scoring reads the *current* question set only, and the plan (Phase 4 task
1) describes "the" interest test as a single thing to draft and approve,
not a versioned series. Adding a `version` column and coexistence logic
would be extra schema and code with no feature depending on it yet.

The trade-off this creates: if the interest test is ever revised after
students have already answered it, this migration's re-run wipes the old
question/option rows, and any existing `interest_answers` rows that still
point at those old `question_id`/`option_id` values become orphaned
references (the FKs (**foreign keys**, columns that must point at a real
row elsewhere) would fail on delete, or the rows would silently point at
nothing meaningful) -- so those old answers can no longer be interpreted
correctly, and affected students would need to retake the test. This is
acceptable for now because the test has not shipped to real users yet, but
whoever revises the question set after launch should read this entry first
and plan for a real migration strategy (versioning, or requiring an
account-wide retake) rather than assuming a plain re-run is safe.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 3 describes
      current save/retake behavior; it does not promise version history,
      consistent with this decision)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entry
      for `1fa628967fac_seed_approved_interest_test.py` points here)
- [ ] No upstream doc update needed
