# 0003 - Interest-Test Data Provenance

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

Phase 4's plan (task 1) requires the interest test's 20 questions to be
"drafted in chat and approved by the product owner before seeding." The
seed data migration (`1fa628967fac_seed_approved_interest_test.py`) loads
those questions from `backend/data/interest_test.json`.

During review, this file looked unverified: it was **untracked** (not yet
committed to **git**, the tool that tracks file history), it had **no prior
git history** to check against, and its own `"approved_by"` field only
asserted approval without saying where or when that approval happened. On
first pass, the rules reviewer treated this as a possible fabrication by the
build step and blocked the phase pending investigation.

## Decision

The file's content is genuine, and its metadata was corrected to say so
plainly. What actually happened:

- The 20 questions were drafted earlier in the product owner's own chat
  session (not invented during this build step), shown to them as a full
  table, and approved in that same conversation ("1. approve") **before**
  the Phase 4 build started.
- `backend/data/interest_test.json` was saved into the repository for the
  first time as part of this build session -- which is exactly why `git`
  showed no earlier history for it. No history existing is expected for a
  new file, not evidence against it.
- A byte-for-byte comparison confirmed the seeded question and option text
  matches what the product owner actually approved in chat -- nothing was
  changed, added, or reworded during seeding.
- The `"approved_by"` field was rewritten from a bare, self-asserting claim
  to a description that says who approved it and how:
  `"product owner, in-session chat approval 2026-09-12"`, plus a new
  `"drafted_by"` field: `"assistant draft, reviewed option-by-option by the
  product owner before approval"`. No question, option, or interest-area
  content changed -- only these two metadata fields.

The reviewer re-ran the check against the corrected file and approved the
phase.

## Reason

Two things were true at once, and both needed to be handled rather than
picked between: the file's *content* was legitimate (it matched what was
actually approved), but its *metadata* did not yet say enough for a
reviewer -- or a future reader with no memory of the chat session -- to
tell that on sight. Fixing only the metadata (not re-approving or
re-drafting the questions) was the smallest correct fix, because the
underlying facts didn't need to change, only how clearly the file states
them.

This is recorded here, rather than left as an unremarked review note,
because the same shape of question -- "is this seed data real or was it
just invented?" -- will come up again for any future data migration that
loads product owner-approved content. The fix here (a metadata field that
names who approved something and how, not just that it was approved) is
the pattern to repeat.

## Impact

- [ ] Workflow doc updated (no behavior changed, so none needed)
- [x] Reference doc updated (`docs/reference/folder-structure.md` already
      lists `backend/data/interest_test.json` and the seed migration that
      loads it)
- [ ] No upstream doc update needed
