# 0014 - AI summary focuses on top strengths and interests

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

The first live GPT-5 summary was accurate, but half of it listed what the student **isn't** into. For example: "lower interest in Business & Management, Law & Governance…" and "Education & Humanities currently shows no interest."

For a 17-year-old, a list of weak areas reads as discouraging. The product owner asked for a softer tone.

## Decision

The system prompt in `backend/app/services/ai_summary.py` now tells GPT-5 to:
- focus on the student's **top 2–3 subject strengths** and **top 2–3 interests**, and what they could mean together,
- **leave out** low or zero scores, and never say the student has "no" or "low" interest in anything,
- talk only about subject strengths when there are no interest scores yet,
- use a warm, supportive tone.

**Enforced in code, not just asked for.** A live check showed GPT-5 still listed weak areas despite the prompt. So `_build_user_message` now sends only the **top 3 subject groups** and the **top 3 non-zero interest areas**. The model can't mention what it never receives.

Nothing else changes: names + scores only (decision `0010`), the 6-second limit (`0012`) and the 120-word cap (`0013`).

## Reason

- Students act on what's highlighted. Naming weak areas adds worry without helping them choose.
- The charts still show every score, so no information is hidden from the student.
- It matches decision `0007`, where the "likely to love" list already drops 0-score areas.

## Impact

- [x] Workflow doc updated
- [ ] Reference doc updated
- [ ] No upstream doc update needed
