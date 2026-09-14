# 0015 - Phase 8 was built before its PRD and plan

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

The project rule is: non-trivial work is built **from a plan**, and the plan is agreed **before** coding starts (`CLAUDE.md`, "Build From the Plan").

On 2026-09-14 the product owner said the website looked unfinished and the spider chart looked broken. The redesign was built straight away, checked in a browser, and committed as **Phase 8** (commit `9fe75b1`). It had no PRD, no plan, no Definition of Done, and no roadmap entry.

## Decision

- **Keep the code.** Don't revert it to redo it by the book.
- **Write the docs after the fact:** `docs/prd/ui-redesign-prd.md`, `docs/plan/ui-redesign-plan.md` (with a Definition of Done), and a Phase 8 entry in `docs/product-roadmap.md`.
- The docs describe **what was actually built**, not an earlier intent.
- Every Definition of Done item says whether it was really checked, and how. Open items stay unticked.
- Phase 8 stays **in-progress** on the roadmap until its open checks pass.

## Reason

- The change is client-only and looks-only: no backend, API or database file changed. Throwing it away to rebuild it in order would add no safety.
- Docs written afterwards can match the code exactly.
- Marking unchecked items honestly keeps the gap visible. In particular, the logged-in pages weren't browser-checked before the commit.
- **Lesson:** for the next change bigger than a small fix, write and agree the plan first, even when the request feels urgent.

## Impact

- [x] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
