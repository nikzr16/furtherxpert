# Interest Test Rotation Implementation Plan

> **Quick summary**
> - **What:** how to build the 300-question bank, the 40-question sets, and the rotate button. The PRD (`docs/prd/interest-test-rotation-prd.md`) says *what* and *why*; this plan says *how*.
> - **Who uses it:** whoever builds, reviews or tests Phase 9.
> - **Now:** Draft (2026-09-14). Nothing is built yet. Building starts only after the product owner agrees this plan and the PRD.
> - **If the build must differ from this plan:** don't edit the plan. Add a note in `docs/decisions/`.

> **Type:** Plan | **Must stay current:** No -- record divergences in decision log, rewrite only during re-planning

<!-- AI Context
Role: This document describes *how* Phase 9 (interest test rotation) is built,
not *what* or *why*. Read `docs/prd/interest-test-rotation-prd.md` first, then the
main PRD sections it changes (`docs/prd/furtherxpert-prd.md` section 3, T1, T6).
Build steps 9.1 to 9.4 in order. 9.1 (the questions) needs the product owner's
approval before anything is loaded. Never mark a question "approved" without it.
Do not rewrite this document during coding. If the implementation diverges from
this plan, add an entry to the decision log instead.
-->

## Overview

Today there's one fixed list of 20 questions, shared by everyone. After this phase:

1. A **bank** of 300 approved questions lives in the database.
2. Each student gets their own **set** of 40 questions, saved in the database.
3. Answers belong to a set. Scores come from the student's latest **finished** set.
4. A **rotate** request swaps an unfinished set for a new one.

The work has 4 steps: **9.1** questions, **9.2** backend, **9.3** page, **9.4** docs.

## Technical Approach

1. **Sets are saved rows, not worked out on the fly.** A set is stored when it's made. So a part-finished set comes back exactly the same, in the same order.
2. **Picking a set is a pure function** (no database inside), like the scoring code. It takes the bank, the student's history, and a random-number source. So tests can feed it a fixed **seed** (a starting number that makes "random" picks repeatable).
3. **"Seen" history comes from old set rows.** Old sets keep their question list, which isn't personal. Only their answers get deleted.
4. **Append questions, don't wipe.** A new data migration adds questions 21–300 by number. Questions 1–20 keep their ids. This avoids the wipe problem warned about in decision `0004`.
5. **One request loads the page.** `GET /me/interest-test` returns the questions and saved answers together. With 2 separate requests, one could make a new set while the other returned the old one.
6. **Scoring formula stays the same.** `interest_area_scores()` doesn't change. Only its inputs change: picks and "most picks possible" now come from one set.

## System Components

| Component | Responsibility |
|---|---|
| `backend/data/interest_test.json` | The bank: 300 questions, with approval notes for each batch |
| `backend/app/models/interest_test.py` | New `InterestTestSet` and `InterestTestSetQuestion` models. `InterestAnswer` gains `set_id` |
| `backend/migrations/versions/<new>_add_interest_test_sets.py` | Schema: the 2 new tables, `interest_answers.set_id`, the new unique rule. Clears old 20-question answers and cached analyses |
| `backend/migrations/versions/<new>_load_interest_question_bank.py` | Data: adds questions 21–300 from the JSON file, matched by question number |
| `backend/app/services/question_sets.py` | Pure function `draw_set()`: picks 40 balanced, fresh questions |
| `backend/app/services/interest_test.py` | Get or create the current set, rotate, save answers (set-aware), progress, answer clean-up |
| `backend/app/services/analysis.py` | Reads picks and "most picks possible" from the latest finished set |
| `backend/app/schemas/interest_test.py` | New `InterestTestSetOut` response shape |
| `backend/app/api/me.py` | `GET /me/interest-test`, `POST /me/interest-test/rotate` |
| `backend/app/api/interest_test.py` | Removed, with its router line in `main.py` (public `GET /interest-test`) |
| `client/src/api.js` | `getMyInterestTest`, `rotateMyInterestTest`. Removes `getInterestTestQuestions` |
| `client/src/pages/InterestTest.jsx` | One load call, "N of 40", the rotate button with a confirm step, a "new set" note |

## Processing Flow

**A. Opening the Interest Test page** (`GET /me/interest-test`)
1. Lock the student's row, so 2 tabs opening at once can't make 2 sets.
2. Find the student's latest set.
3. **No set, or the latest set is finished:** draw a new set (flow C), then save it.
4. **Latest set is unfinished:** keep it.
5. Return the set's 40 questions in order, the saved answers, `answered`, `total` (40), `complete`, and `has_finished_set` (true if an earlier finished set still feeds My Results).

**B. Rotating** (`POST /me/interest-test/rotate`)
1. Lock the student's row.
2. If the latest set is unfinished: mark it `discarded_at = now` and delete its answers. Keep its question list for "seen" history.
3. Draw and save a new set. Clear the cached analysis.
4. Return the new set, in the same shape as flow A.

**C. Drawing a set** (`draw_set()`, pure)
1. **Inputs:** each bank question's 4 areas; the student's past sets, oldest first; a random-number source.
2. **Fresh pool:** questions in no past set, shuffled.
3. **Top-up pool:** questions seen before, but not in the most recent set, oldest set first (shuffled within each set).
4. Walk the fresh pool, then the top-up pool. Add a question only if no area would go over **20**.
5. Stop at 40. If any area is under **16**, try again with a new shuffle (up to 50 tries).
6. If all tries fail, return the best try, and log that the balance range wasn't met. (No student data goes in the log.)

**D. Saving answers** (`PUT /me/interest-answers`)
1. Find the current set (the latest one not discarded). Reject questions that aren't in it (**400** = "bad request" error).
2. Upsert (update or insert) each answer, as today (decision `0008`). Clear the cached analysis.
3. If the set now has 40 answers and `completed_at` is empty: set `completed_at`. Then delete the answers of any older finished set. Only the newest finished set's answers are kept.

**E. My Results** (`GET /me/analysis`)
1. Find the latest set with `completed_at` set.
2. **None:** `interest_test_complete = false`, all 9 areas at 0, "likely to love" empty (decision `0008`).
3. **Found:** picks = that set's answers per area. Most picks possible = that set's questions offering each area. Then run `interest_area_scores()` as today.

## Dependencies

| Dependency | Purpose |
|---|---|
| PostgreSQL row lock (`SELECT ... FOR UPDATE`) | Stops 2 sets being made at once for one student |
| Python `random.Random` | Seedable random picks for `draw_set()` |
| Alembic | The schema migration and the question bank data migration |

No new packages.

## Data changes

| Table | Change |
|---|---|
| `interest_questions` | No schema change. `n` now runs 1–300 |
| `interest_test_sets` (new) | `id`, `user_id` (links to `users`, deleted with the account), `created_at`, `completed_at` (empty until 40 answered), `discarded_at` (empty unless rotated away) |
| `interest_test_set_questions` (new) | `set_id` (deleted with the set), `question_id`, `position` (1–40). One row per question per set. Unique on (`set_id`, `position`) and on (`set_id`, `question_id`) |
| `interest_answers` | Add `set_id` (required, deleted with the set). Unique rule changes from (`user_id`, `question_id`) to (`set_id`, `question_id`). Existing rows are deleted first, because they belong to no set |
| `analysis` | All rows deleted once, so every student's scores are recomputed |

## Implementation Phases

### Step 9.1: The 280 new questions

**Goal:** 280 new approved questions in `backend/data/interest_test.json`.

**PRD sections:** 3, 6; acceptance criteria 1, 2, 11.

**Tasks:**
1. **Work out area targets.** The current 20 questions tag Business & Management 8 times and every other area 9 times. The full bank needs 1,200 tags: 3 areas at 134 and 6 areas at 133. Subtract the current counts to get each area's target for the 280 new questions.
2. **Draft in batches of 40** (7 batches), shown in chat as a table: question, 4 answers, each answer's area.
   - Each question's 4 answers use 4 **different** areas.
   - Plain English for a 17-year-old, with Malaysian settings where it fits. Keep the style of the current 20.
   - No repeats or near-repeats of earlier questions.
3. **The product owner reviews each batch.** Fix what they ask for. Move to the next batch only after "approved".
4. **Save each approved batch** into the file as questions 21–300, and bump `version`. Record approval per batch, for example `"approved_by": "product owner, in-session chat approval 2026-09-14, batch 1 (questions 21–60)"`. Pattern from decision `0003`.
5. **Data file test** (`backend/tests/test_interest_bank.py`): 300 questions; `n` runs 1–300 with no gaps; every question has 4 answers in 4 different areas, plus "None of the above"; no duplicate question text; every area tagged 133 or 134 times.

**Check:** the data file test passes, and every batch has a recorded approval.

### Step 9.2: Backend

**Goal:** sets, rotation and set-based scoring work through the API.

**PRD sections:** 3, 5, 6, T1–T3. Main PRD T1, T4, T6.

**Tasks:**
1. **Models + schema migration** from the Data changes table above.
2. **Question bank data migration:** insert questions and answers for each `n` not yet in the database. If an `n` already exists, leave it alone. Safe to re-run.
3. **`question_sets.py`:** `draw_set()` per flow C.
4. **`interest_test.py`:** `get_or_create_current_set`, `rotate_set`, set-aware `save_answers`, `get_progress` (current set only, never creates), and the answer clean-up per flow D.
5. **Routes** in `me.py`: `GET /me/interest-test`, `POST /me/interest-test/rotate`. Both go through `get_current_user` and are scoped to that user.
6. **Remove** `app/api/interest_test.py` and its router in `main.py`.
7. **`analysis.py`:** set-based picks and "most picks possible" per flow E. Update comments that say "20".
8. **Golden tests:**
   - Give each golden student a **fixed** 40-question set, created directly in the test (not drawn), so results don't depend on randomness.
   - Rewrite `interest_picks` for those 40 questions.
   - **Work out every expected interest score and Best Fit by hand** from T1, before running the code. Never copy them from the code's output.
   - Note in the change that these numbers changed on purpose, because of the new rule.
9. **Update the rules skill** `.claude/skills/proj-furtherxpert-rules/SKILL.md` (20 → 40, set-based counts), then run `python .claude/skills/validate-config/scripts/validate_config.py`.

**Check:**
- `docker compose exec backend uv run pytest` passes, including the new tests in the Testing Strategy below.
- `alembic upgrade head` runs on a copy of today's database, and `alembic downgrade -1` works for the schema migration.

### Step 9.3: Interest Test page

**Goal:** the page uses sets and has the rotate button.

**PRD sections:** 3, 5 (criteria 5–7, 12).

**Tasks:**
1. **`api.js`:** add `getMyInterestTest(authedFetch)` and `rotateMyInterestTest(authedFetch)`. Remove `getInterestTestQuestions`.
2. **Load** with the one `getMyInterestTest` call. Progress shows "N of 40 answered".
3. **"Get new questions" button** next to the progress bar, as a secondary button.
   - **0 answers:** rotate right away.
   - **1 or more answers:** show an inline 2-step confirm, like Account's delete. For example: "This clears your 12 answers and gives you 40 new questions." Buttons: "Get new questions" and "Keep these".
   - While rotating: disable the button, show a spinner, then scroll to the top.
4. **"New set" note:** if `has_finished_set` is true and `answered` is 0, show: "Here's a fresh set of 40 questions. Your last results stay on My Results until you finish this set."
5. **Finished card:** unchanged, but it appears after 40 answers.
6. **Find leftover "20"s:** search `client/src` for text that says 20 questions (Home, My Results, AI summary messages), and change it to 40.

**Check:**
- `npm run build` passes.
- In a browser, at 375px and 1200px wide: start a set, answer a few, reload (same set), rotate with the confirm, finish all 40, open the page again (new set, and My Results still shows the chart).
- The product owner logs in for this check, because Claude can't type the password.

### Step 9.4: Docs

**Goal:** docs match the new behaviour.

**Tasks:**
1. **Roadmap:** add Phase 9 with this PRD and plan. Mark it `shipped` only when every check passes.
2. **Workflow doc** `docs/furtherxpert-workflow.md`: Flow 3 (sets, resume, rotate) and Flow 4 (set-based scores).
3. **Reference** `docs/reference/folder-structure.md`: new files, routes and tables. Remove `app/api/interest_test.py`.
4. **Decision entry** `docs/decisions/0018-interest-test-question-bank-and-sets.md`: it builds on `0004` (questions now appended, not wiped) and `0008` (completeness now per set, 40 questions).
5. **`CLAUDE.project.md`:** update "20-question interest test" to the 300-question bank with 40-question sets.
6. Run the session-close checklist in `docs/documentation-standard.md`.

## Testing Strategy

Expected numbers in every test are worked out **by hand from the rules**, never copied from the code's output.

- **Data file** (`test_interest_bank.py`): PRD criteria 1–2.
- **Set drawing** (`test_question_sets.py`, pure, seeded):
  - 500 draws: always 40 different questions, every area 16–20 times.
  - No overlap with past sets while 40 or more unseen questions remain.
  - When fewer than 40 unseen remain: all unseen are used, and none come from the most recent set.
  - The same seed gives the same set.
  - A small hand-made bank where balance is impossible: returns 40 questions and doesn't crash.
- **API** (`test_student_input.py` and a new `test_interest_sets.py`):
  - First open makes a set. Reopening an unfinished set returns the same questions, order and answers.
  - After 40 answers, reopening makes a new set, and `/me/analysis` still shows the finished set's scores.
  - Rotate discards the answers, gives a new set, and doesn't touch a finished set's scores.
  - An answer for a question outside the current set gets a 400.
  - `GET /me/interest-answers` never makes a set.
  - Finishing a second set deletes the first set's answers.
  - Student B's token can't see or change student A's set.
  - `DELETE /me` removes sets, set questions and answers.
- **Analysis** (`test_analysis.py`): a hand-made set where one area appears in 16 questions and another in 20. Checks the scores use those counts, not the whole bank's.
- **Golden tests:** updated as in Step 9.2 task 8.
- **Client:** `npm run build` and the browser check in Step 9.3.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| 280 questions is a lot to review | Tired reviewing lets weak or repeated questions through | 7 batches of 40. The data file test catches exact duplicates and bad tags |
| New questions lean towards some areas | Unfair sets or charts | Area targets per batch (Step 9.1 task 1), and the 133–134 bank test |
| Late in a student's history, the leftover questions can't make a balanced set | A set falls slightly outside 16–20 | Retry with new shuffles, then return the best try and log it. Tested with a hand-made bank |
| Two tabs open the page at the same moment | 2 sets made for one student | Row lock in flows A and B, and a test that calls it twice |
| The migration deletes existing test answers | Dev accounts must retake the test | Expected, and stated in the PRD. There are no real users yet |
| Golden numbers get copied from the code | Wrong rules pass the tests | Work them out by hand first. The reviewer checks one student's numbers by hand |
| 40 questions make a long page on a phone | Students give up partway | Progress is saved on every answer. The sticky progress bar shows how far there is to go |

## Roadmap Phase

**Phase:** Phase 9, Interest test rotation. It gets added to `docs/product-roadmap.md` once the PRD and this plan are agreed.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/product-roadmap.md` | Roadmap | Phase 9 status and checks |
| `docs/prd/interest-test-rotation-prd.md` | Intent | What this plan builds, and its acceptance criteria |
| `docs/prd/furtherxpert-prd.md` | Intent | The main rules this feature changes (section 3, T1, T6) |
| `docs/furtherxpert-workflow.md` | Workflow | Flows 3 and 4, updated in Step 9.4 |
| `docs/reference/folder-structure.md` | Reference | Where the new files live |
| `docs/decisions/0003-*.md`, `0004-*.md`, `0008-*.md` | Decision log | Question approval notes, the no-wipe risk, and the completeness rule this plan builds on |

## Open Questions

- [ ] How does the product owner want to review the 280 questions? This plan assumes 7 batches of 40 in chat.
- [ ] Is a 16–20 balance range per area OK?
