# Why This Diploma? Implementation Plan

> **Quick summary**
> - **What:** how to add a "Why this diploma?" section to every diploma in Best Fit. The PRD (`docs/prd/result-explanations-prd.md`) says *what* and *why*; this plan says *how*.
> - **Who uses it:** whoever builds, reviews or tests Phase 10.
> - **Now:** Draft (2026-09-14). Nothing is built yet. Building starts only after the product owner agrees this plan and the PRD.
> - **If the build must differ from this plan:** don't edit the plan. Add a note in `docs/decisions/`.

> **Type:** Plan | **Must stay current:** No -- record divergences in decision log, rewrite only during re-planning

<!-- AI Context
Role: This document describes *how* Phase 10 (per-diploma explanations) is built,
not *what* or *why*. Read `docs/prd/result-explanations-prd.md` first, then main
PRD T1, T2 and T6.
Hard rule: this phase changes NO score, rank, Best Fit choice, program order or
eligibility verdict. Existing golden numbers and eligibility tests must stay
exactly the same.
Do not rewrite this document during coding. If the implementation diverges from
this plan, add an entry to the decision log instead.
-->

## Overview

`GET /me/analysis` already knows everything behind a suggested diploma. It just doesn't keep it:
- the area the diploma matches, and why that area is in the student's top 3,
- the rule tree the checker passed,
- the verdict, and where the diploma sits in the area's list.

This phase keeps that working, turns it into plain-words sentences in pure functions, and shows it under each diploma on My Results.

The work has 3 steps: **10.1** backend, **10.2** page, **10.3** docs.

## Technical Approach

1. **Show one real way the rules are met.** Add a pure function in `eligibility.py` that returns **one valid matching**: which subject met which rule. It uses the same backtracking as `tree_is_satisfiable`, so it can never show a matching the checker wouldn't accept. Each subject is used once.
2. **Readable and stable matching.** A matching is found in a fixed order:
   - named-subject rules first (`subject`, `one_of`, `any`), then "N more subjects" rules (`uncounted`) last,
   - candidate subjects sorted by best grade, then subject code.

   Changing the order changes which valid matching is found, never **whether** one exists. So verdicts can't change. The sorting also removes Python's random set order, so a student sees the same grades on every visit.
3. **A new pure module, `services/explanations.py`**, builds the `why` object: area link sentences, rule lines, still-needed lines, and the position line. No database, no clock.
4. **`analysis.py` passes in what it already has**, plus subject names and program NEC fields it loads once.
5. **The backend owns the words.** The page only displays them, like eligibility `reasons` today.
6. **Old cached results are cleared** by a small data migration, so every student gets explanations on their next visit.

## System Components

| Component | Responsibility |
|---|---|
| `backend/app/services/eligibility.py` | New pure `find_matching(general_rules, program_rules, grades)`: one valid matching per rule, in the fixed order. `evaluate_eligibility` is unchanged |
| `backend/app/services/explanations.py` (new) | Pure `explain_program(...)`: builds `match`, `rules`, `still_needed`, `position` |
| `backend/app/services/analysis.py` | Loads subject names; keeps `nec_code`/`nec_name`, raw rules and the per-area count; calls `explain_program` for each shown program |
| `backend/app/schemas/analysis.py` | New `ProgramWhy` and `RuleSection` models; `BestFitProgram.why` |
| `backend/migrations/versions/<new>_clear_analysis_cache_for_why.py` | Deletes every `analysis` row once |
| `client/src/components/WhyThisDiploma.jsx` (new) | The open/close section under one diploma |
| `client/src/pages/MyResults.jsx` | Renders `WhyThisDiploma` under each program row |

## Processing Flow

**A. Finding the matching** (`find_matching`, pure)
1. Combine syarat am and syarat khas like `combine_rule_trees`. Remember which rules came from which side.
2. Order the rules: named-subject rules first, `uncounted` last. Keep each side's original order within those groups.
3. Backtrack like `_ways_all`, but carry the choice made at each rule:
   - `subject` → that subject,
   - `one_of` → the `count` best qualifying subjects,
   - `any` → the first branch that works, and its choices,
   - `uncounted` → the `count` best remaining subjects.
4. Return, for each rule in its **original** order, the side (general or program), the rule, and the chosen subjects with their grades. Return `None` if nothing works (this can't happen for a shown program; a test checks it).

**B. Building one diploma's `why`** (`explain_program`, pure)
1. **`match`**
   - "This is a {field} diploma: its field of study, {nec_name} (code {nec_code}), is part of {area}."
   - Excel side, if the area is in `likely_to_excel`: "{area} is #{rank} in what you're likely to excel in, at {score}%, from your {group} ({score}%) and {group} ({score}%) grades."
   - Love side, if the area is in `likely_to_love`: "{area} is #{rank} in what you're likely to love, at {score}%: you picked a {area} answer in {picks} of the {offered} questions that offered one."
   - Sweet spot, if both: the Sweet spot sentence.
   - The short "{field}" word comes from a small hand-written map of NEC 3-digit fields (for example `041` → "business", `0412` → "finance"). Without a map entry, the sentence starts "Its field of study, …".
2. **`rules`**: 2 sections, "General UPU rules (syarat am)" and "This diploma's rules (syarat khas)". One line per rule:
   - `subject`: "Matematik — needs C, you have A+"
   - `one_of`: "One of Fizik / Kimia / Biologi at C — Fizik (A+)"
   - `any`: the line for the branch used
   - `uncounted`: "2 more subjects at C or better — Bahasa Inggeris (A), Kimia (A)"
   - An empty syarat khas: "No extra subject rules beyond the general ones."
   - Bumiputera-only: add "Only open to Bumiputera students — you qualify." to the diploma's section.
3. **`still_needed`**: Eligible → "Nothing else needed — no interview or test." Conditional → one friendly line per existing reason, for example "Requires interview/test" → "You'll need to pass an interview or test."
4. **`position`**: "{n} of {total} diplomas you can apply for in {area}. Eligible ones are shown first, then A to Z. See all of them on Explore."

## Dependencies

No new packages. Existing data: `programs.nec_code`, `programs.nec_name`, `general_requirements.rules`, `program_requirements.rules`, `subjects.code` / `subjects.name_ms`, and `interest_areas.subject_groups`.

## Implementation Phases

### Step 10.1: Backend

**Goal:** each Best Fit diploma in `GET /me/analysis` carries `why`. Every existing number and verdict stays the same.

**PRD sections:** 3, 5, 6, T1, T2. Main PRD T1, T2, T6.

**Tasks:**
1. **`eligibility.py`:** add `find_matching`, per Processing Flow A. Don't change `evaluate_eligibility`.
2. **`explanations.py`:** add `explain_program` and the small NEC field-word map, per Processing Flow B.
3. **`analysis.py`:**
   - load `{subject_code: name_ms}` once,
   - keep `nec_code`, `nec_name` and the raw rules in the internal program dicts (they aren't returned, except through `why`),
   - keep each area's full Eligible + Conditional count before the top-3 cut,
   - keep excel group breakdowns and love picks / offered per area,
   - call `explain_program` for each shown program.
4. **Schemas:** `ProgramWhy { match: list[str], rules: list[RuleSection], still_needed: list[str], position: str }`, `RuleSection { title: str, lines: list[str] }`.
5. **Migration:** clear the `analysis` table once. The downgrade does nothing (it's a cache).
6. **Unit tests** (`tests/test_find_matching.py`, `tests/test_explanations.py`), with expected lines written by hand:
   - `find_matching`:
     - the counts-once trap (the same case as the existing eligibility test),
     - `one_of` with 2 needed,
     - an `any` choosing its second branch,
     - `uncounted` taking the best leftover grades,
     - the same result over 50 runs with the grades dict shuffled,
     - for 200 random grade sets and every real rule tree in the snapshot: `find_matching` returns a result exactly when the checker's grade tree passes.
   - `explain_program`:
     - excel only, love only, sweet spot,
     - an empty syarat khas,
     - Bumiputera-only,
     - Eligible vs Conditional,
     - a missing NEC field word,
     - the position line.
7. **Golden tests:** add hand-worked `why` expectations:
   - **Amir** on `UE4481001` (Bumiputera-only, has syarat khas): every rule line worked out by hand from its e-Panduan rules and his grades, in the fixed order.
   - **Rahman** on `UE4213001` (Conditional, interview): "You'll need to pass an interview or test".
   - **One diploma with no syarat khas** (for example `UE4343004`): the "No extra subject rules" line.

   Existing chart, Best Fit and verdict numbers must not change.
8. **Privacy tests:**
   - the `why` text contains no race value and no interest test question or answer text,
   - the AI summary request is unchanged (`test_ai_summary.py` payload check still passes).

**Check:** `docker compose exec backend uv run pytest` passes, with golden numbers unchanged.

### Step 10.2: My Results page

**Goal:** every diploma has an open/close "Why this diploma?" section.

**PRD sections:** 3, 5 (criterion 10).

**Tasks:**
1. **`WhyThisDiploma.jsx`:** a native `<details>`/`<summary>` labelled "Why this diploma?", starting closed. Inside:
   - "Why it matches you" (`match`),
   - "How you meet the entry rules" (each `rules` section as a titled list),
   - "Anything still needed" (`still_needed`),
   - the `position` line, with a link to Explore.
2. **`MyResults.jsx`:** place it at the bottom of each program row, under the existing `ReasonList`. If `why` is missing (for example an old cached result), render nothing.
3. **Build and lint:** `npm run build`, `npx oxlint src` — no new warnings.

**Check:** a by-hand browser check at 375px and 1200px wide, with a real account:
- open and close with a mouse, and with Tab + Enter,
- grades in the text match the SPM Results page,
- scores match the chart labels.

The product owner logs in for this check, because Claude can't type the password.

### Step 10.3: Docs

**Tasks:**
1. **Roadmap:** add Phase 10. Mark it `shipped` only when every check passes.
2. **Workflow doc:** Flow 4 (the `why` step) and the My Results page section.
3. **Reference doc:** new files, schema fields, migration.
4. **Rules skill** `.claude/skills/proj-furtherxpert-rules/SKILL.md`: explanations must use the checker's own matching and the charts' rounding. Then run `python .claude/skills/validate-config/scripts/validate_config.py`.
5. **Decision entries** for anything built differently from this plan. Check `docs/decisions/` for the next free number first, since other sessions may add entries.

## Testing Strategy

- **Expected lines and numbers are worked out by hand** from the rules and the e-Panduan text, never copied from the code's output.
- **`find_matching` must agree with the checker.** A test compares them over the real snapshot's rule trees and many random grade sets.
- **Stability:** the same inputs in a shuffled order give the same lines.
- **Regression:** all existing backend tests keep passing, including golden numbers and eligibility spot-checks.
- **Client:** build, lint, and the by-hand browser check in Step 10.2.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The explanation shows a matching the checker wouldn't accept | Misleading "you meet this rule" | Same backtracking engine, and an agreement test over every real rule tree |
| A different valid matching shows on each visit | Confusing, looks buggy | Fixed rule order, and subjects sorted by grade then code. Shuffle test |
| The rule order picks an odd-looking matching (for example, a strong grade used for "2 more subjects") | Harder to read | Named-subject rules first, `uncounted` last |
| Some rule trees in the snapshot use shapes the sentences don't cover | Blank or wrong lines | Test every real rule tree renders a line per rule |
| The NEC field word is missing or too vague | Awkward sentence | Fallback wording without the field word |
| Race leaks through the Bumiputera line | Privacy breach (PDPA) | Fixed wording "you qualify", and a test that no race value appears |
| Old cached results have no `why` | Blank section | The migration clears the cache, and the page hides a missing `why` |
| Long rule lists crowd the phone layout | Hard to read | Starts closed, and checked at 375px |

## Roadmap Phase

**Phase:** Phase 10, Why this diploma. It gets added to `docs/product-roadmap.md` once the PRD and this plan are agreed.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/product-roadmap.md` | Roadmap | Phase 10 status and checks |
| `docs/prd/result-explanations-prd.md` | Intent | What this plan builds, and its acceptance criteria |
| `docs/prd/furtherxpert-prd.md` | Intent | The Best Fit, area and eligibility rules being explained (T1, T2, T6) |
| `docs/furtherxpert-workflow.md` | Workflow | Flow 4 and the My Results page, updated in Step 10.3 |
| `docs/reference/folder-structure.md` | Reference | Where the new files live |
| `docs/decisions/0005-*.md`, `0020-*.md` | Decision log | The counts-once matching and set-based love counts this plan explains |

## Open Questions

- [ ] Rank Best Fit diplomas by fit instead of A to Z, in a later phase?
