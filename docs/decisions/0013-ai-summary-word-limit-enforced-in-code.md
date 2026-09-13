# 0013 - The 120-Word Limit Is Enforced in Code, Not Just Asked For in the Prompt

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

The plan's Phase 7 task 1 states the requirement plainly: "Keep it to 120
words or fewer." That's not a soft style preference -- it's a hard
requirement the Phase 7 Check depends on, and the client's
`AISummaryCard.jsx` renders whatever text it gets back directly, with no
UI-side truncation of its own.

The first implementation relied on the system prompt alone: it tells GPT-5
"Write at most 120 words." A large language model's word count is not a
hard, deterministic property of the request the way a `max_tokens`-style
token cap is -- the model can and does overshoot a word-count instruction
it was given in plain English.

As required by this task, a live check was performed against the real
OpenAI API (a throwaway account, real `.env` `OPENAI_API_KEY`, one real
`GET /me/analysis/summary` call, account deleted afterward). It returned a
`200` in ~6.0 seconds with a summary that was **122 words** -- 2 words over
the limit, despite the system prompt explicitly asking for 120 or fewer.

## Decision

`app/services/ai_summary.py` adds `_enforce_word_limit`, called on every
reply before it's returned or cached: it deterministically counts words in
the response text and, if over `MAX_SUMMARY_WORDS` (120), cuts it down,
preferring to cut at the end of the last full sentence that still fits
within the word budget (so the cut doesn't land mid-sentence); if no
sentence boundary is found in the truncated text, it falls back to a plain
word-count cut. The system prompt's "at most 120 words" instruction is kept
as-is (it still reduces how often truncation is needed at all, and keeps
replies reading naturally most of the time), but it is no longer treated as
the enforcement mechanism -- `_enforce_word_limit` is.

## Reason

**The trade-off accepted:** an over-long reply now sometimes gets cut off
partway through its idea (when no sentence boundary falls within the first
120 words), producing a summary that reads slightly less polished than the
model's original full reply would have.

**Why this was accepted anyway:** the plan's requirement is a hard word
limit, and the live check proved the prompt-only approach cannot reliably
guarantee it -- "ask the model nicely" is not the same thing as "enforce."
A regression here would be silent and easy to miss: nothing in the code
would error, the response would still be `200 OK`, and the only symptom
would be an occasionally-too-long summary a developer might not notice
without counting words by hand. Code-level enforcement is
correct-by-construction (a Python word count is deterministic, unlike an
LLM (Large Language Model) honoring a word-count instruction), and it's
covered by an automated test
(`backend/tests/test_ai_summary.py::test_overlong_reply_is_truncated_to_120_words`)
that configures the mocked OpenAI client to return a deliberately
150-word reply and asserts the response actually returned is 120 words or
fewer -- so this can never silently regress again.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 6 section
      1 step 6 and the Defaults table both describe this and link here)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entry
      for `ai_summary.py` points here)
- [ ] No upstream doc update needed
