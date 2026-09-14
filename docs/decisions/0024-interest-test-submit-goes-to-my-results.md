# 0024 - Interest Test Submit Goes to My Results

> **Date:** 2026-09-15 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

Decision `0023` sent students to the **home page** after they pressed Submit on the Interest Test, taking "main page" to mean the home page. The product owner corrected this (chat, 2026-09-15): after submitting, the student should land on **My Results**.

## Decision

This replaces the redirect target in decision `0023`. Everything else in `0023` stays.

- After Submit, the "Submitted" dialog says "Your answers are saved. Taking you to your results…".
- It goes to `/my-results` after 2.5 seconds, or at once with "Go now".

## Reason

The student has just finished the test, so their new interest chart and Best Fit are the next thing they want to see.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md`, Interest Test page step 5)
- [x] Reference doc updated (`docs/reference/folder-structure.md`, `InterestTest.jsx` row)
