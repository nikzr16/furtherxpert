# 0021 - The 280 New Interest Questions Were Reviewed by the Assistant, Not the Product Owner

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

The rotation PRD (acceptance criterion 11) and plan (Step 9.1) said each batch of the 280 new questions would be shown in chat and approved by the product owner before loading. Decision `0003` set the pattern: the data file must say plainly who approved content, and how.

When the PRD and plan were agreed, the product owner said to review the questions without them: "you review yourself, im lazy man, i just wanna get back and see everything is ready" (chat, 2026-09-14).

## Decision

- The assistant drafted questions 21–300 and reviewed them itself. The batches were **not** shown in chat.
- **How they were checked:**
  - A script checked every question has 4 answers in 4 different areas.
  - It checked every area is tagged 133 or 134 times across the bank.
  - It checked there are no repeated question or answer texts.
  - It listed similar-looking questions, which were read by eye.
  - A read-through fixed wording and 5 answers: 3 repeated answers, and 2 architecture answers moved out of Arts & Design, because architecture sits under Science & Technology's NEC codes (PRD T1).
- `backend/data/interest_test.json` records this in its `bank` field. It says the product owner delegated the review and **did not** review the new questions one by one.
- Questions 1–20 keep their original product owner approval.
- `backend/tests/test_interest_bank.py` checks the file keeps saying so.

## Reason

The product owner's instruction replaces the batch approval step. Recording it honestly follows `0003`: never label content "approved" unless it really was.

## Impact

- [x] Data file metadata updated (`backend/data/interest_test.json` `bank` field)
- [x] Roadmap note (`docs/product-roadmap.md` Phase 9) says the review was delegated
- [ ] Open follow-up: the product owner, or a school counsellor (main PRD section 8), may still want to skim the new questions later
