# 0022 - "Why This Diploma?": Build Details

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

Phase 10 (`docs/prd/result-explanations-prd.md`, `docs/plan/result-explanations-plan.md`) adds a "Why this diploma?" section to every Best Fit diploma. A few build details differ from the plan's wording, or weren't spelled out in it.

## Decision

1. **Rule line wording.**
   - A "one of" rule is written "At least C in 1 of Fizik / Kimia / Biologi — Kimia (A)", not "One of … at C".
   - A list longer than 5 subjects is written as a count: "At least C in 1 of 15 listed subjects — Fizik (A+)". Program Detail still shows the full Malay rule text.
   - A "one of" rule with only one subject reads like a normal subject rule: "Bahasa Melayu — needs C, you have A".
2. **"Either / or" rules get a lead line.** Before the lines for the branch the student meets, the section shows "You meet one of the allowed options:". 31 real diplomas have these rules, some with several subjects in one branch.
3. **Unverifiable notes** (rules grades can't check) read "Check this yourself, as we can't confirm it from grades: …".
4. **Golden checks for real diplomas call the pure functions directly** (Amir on `UE4481001`, Rahman on `UE4213001`), with rules loaded from `GET /programs/{code}`. Best Fit only shows the first 3 diplomas by name, so a given diploma may not appear in a student's list. A separate golden test checks every diploma that does appear.
5. **Agreement test size.** The plan said 200 random grade sets. The build uses 12 random grade sets for **every** real syarat khas row (328 rows, about 3,900 checks), half of them biased towards strong grades. That way both "meets the rules" and "doesn't" are really tested for each rule shape, and the run stays fast.
6. **Data issue found, not fixed here.** Some UiTM diplomas (for example `UE4343004`, `UE4213001`) are marked Bumiputera-only at program level, but not in their rule data. The checker and this explanation both follow the rule data. So the explanation adds no Bumiputera line for them, matching today's verdict. Fixing the data is a separate task, because this phase must not change any verdict.

## Reason

- Shorter, consistent lines read better on a phone, and a count avoids a 15-name wall of text.
- The lead line makes clear the student didn't need to meet every branch.
- Testing every real rule tree matters more than the raw number of random grade sets.
- Explanations must agree with today's verdicts, so a data fix belongs in its own change.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md`: Flow 4 step j2, My Results page, Behavioral Constraints)
- [x] Reference doc updated (`docs/reference/folder-structure.md`: new files, schema field, migration, tests)
- [x] Skill updated (`.claude/skills/proj-furtherxpert-rules/SKILL.md` checklist)
- [ ] Open follow-up: the Bumiputera flag mismatch (item 6), raised as a separate task
