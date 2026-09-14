# 0020 - Interest Test Question Bank and Per-Student Sets: Build Details

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

Phase 9 (`docs/prd/interest-test-rotation-prd.md`, `docs/plan/interest-test-rotation-plan.md`) grows the interest test to a 300-question bank. Each student gets their own 40-question set, and can rotate it. This builds on two earlier decisions:

- `0004` said re-running the Phase 4 seed wipes every question, which would break saved answers.
- `0008` said interest scores only appear once "all 20" questions are answered.

A few build details differ from the plan, or weren't spelled out in it. The plan (Step 9.4) named this entry `0018`, but another session used `0018` and `0019` for Phase 8 fixes first, so this entry is `0020`, and the question-review note is `0021`.

## Decision

1. **Questions are appended, not wiped.** A new data migration (`b8d4f0a52c31`) inserts only question numbers not yet in the database. Questions 1–20 keep their ids. This avoids the risk `0004` warned about.
2. **Completeness is now per set.** `0008`'s gate still applies, but "complete" means the student's **latest finished set** (all 40 answered), not "every question in the database". Scores divide by how many questions **in that set** offer each area.
3. **Set picking is one pass, not up to 50 retries.** The plan's Flow C described shuffle-and-retry. The build instead picks, at each step, the question whose areas are least represented so far. Ties go to the shuffled order. That gives balanced sets (16–20 per area) every time in testing (500 draws), so retries weren't needed. The balance check and warning log are still there.
4. **Picking the pool when fresh questions run low.** With fewer than 40 unseen questions, all of them are used. The rest is topped up from earlier sets, oldest first, one whole set at a time, never the most recent set.
5. **Answering with no set yet is rejected** (`400`), the same as answering a question outside the current set.
6. **`GET /me/interest-answers` keeps its old response shape** (`answers`, `complete`), now scoped to the current set. The new `GET /me/interest-test` carries the extra progress fields (`answered`, `total`, `has_finished_set`).
7. **Golden tests use a fixed set** (bank questions 1–40), created directly in the test, so their numbers never depend on randomness. Their expected interest scores changed on purpose (for example Amir: 9 ÷ 9 = 100.0 became 9 ÷ 18 = 50.0). Each expected file's `_derivation` shows the hand-counted working.
8. **Balanced area slots for new questions.** Before writing questions 21–300, each one was given 4 areas from a rotating pattern that gives every area the same share. Then the questions were written to fit. That's how the bank reached exactly 133 or 134 tags per area.

## Reason

- Appending keeps every existing id valid, so there's no data-loss trap for future bank updates.
- A single balanced pass is simpler than retrying, and more predictable.
- A fixed golden set keeps the "same inputs → same numbers" rule (PRD section 6) testable.
- Keeping `GET /me/interest-answers` unchanged avoids breaking anything that already uses it.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flows 3, 4 and page 5)
- [x] Reference doc updated (`docs/reference/folder-structure.md`: files, routes, tables)
- [x] Skill updated (`.claude/skills/proj-furtherxpert-rules/SKILL.md`: set-based max picks)
