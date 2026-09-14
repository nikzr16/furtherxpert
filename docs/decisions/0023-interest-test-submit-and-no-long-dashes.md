# 0023 - Interest Test Submit Button, and No Long Dashes in Explanations or the AI Summary

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

After trying Phases 9 and 10, the product owner asked for 2 changes (chat, 2026-09-14):

1. The green "You've answered every question" card at the **top** of the Interest Test page wasn't wanted. They asked for a **Submit** button at the bottom. It should show "Submitted" in a dialog, then go to the main page.
2. No long dashes ("—") in the explanations or while the summary is written.

This differs from the rotation plan (Step 9.3 task 5, the finished card) and from the example wording in the Phase 10 PRD.

## Decision

**Interest Test page**
- The top "finished" card is removed.
- A card at the bottom holds a **Submit** button.
  - Until all 40 are answered, it's disabled and says how many are left.
  - Pressing it asks the server (`GET /me/interest-answers`) whether every answer really saved.
  - If yes: a "Submitted" dialog appears, then the page goes to the **home page (`/`)** after 2.5 seconds, or at once with "Go now".
  - If not: an error asks the student to check their answers.
- **No new server request.** Answers still save one by one, and the set is still marked finished the moment the 40th answer saves. So Submit is a confirmation step for the student: My Results already has the chart even if they never press it.
- "Main page" was taken to mean the home page, the site's main page. My Results is one click away from there.

**No long dashes**
- The "Why this diploma?" wording now uses colons, commas and full stops. For example: "Bahasa Melayu: needs C, you have A" and "Nothing else needed. No interview or test."
- Text from data, such as program names or rule notes, is also cleaned in code (`explanations._no_dashes`).
- The AI summary prompt asks for no long dashes. `ai_summary._remove_long_dashes` also removes them in code before the summary is saved, because a prompt is only a request (the lesson from decision `0013`).
- Migration `d1f6b2c74e53` clears cached results once, so saved explanations and summaries are rebuilt without dashes.
- Eligibility reasons for Not Eligible programs (for example "Needs C in BM — you have D") are unchanged. Best Fit never shows them.

## Reason

- The product owner's direct request.
- Enforcing "no dashes" in code follows the project rule that limits which matter are enforced in code, not only in prompts.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md`: Interest Test page, Behavioral Constraints)
- [x] Reference doc updated (`docs/reference/folder-structure.md`: Interest Test page, AI summary, migration)
- [ ] Open question: should Not Eligible reasons lose their dashes too, if they're ever shown?
