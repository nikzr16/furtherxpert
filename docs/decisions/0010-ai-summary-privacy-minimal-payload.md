# 0010 - The AI Summary Prompt Carries Only Area/Group Names + Scores

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

Phase 7 (PRD T4, T7) adds `GET /me/analysis/summary`, which asks GPT-5 (via
the OpenAI API) to write a short, plain-English summary of a student's own
scores. This is the first time any student data leaves the app's own
infrastructure and goes to a third party. PRD T4's privacy rule ("Collect
only what's needed") and the PDPA 2010 (Malaysia's data-protection law) both
apply directly: whatever crosses that boundary has to be the minimum needed
to do the job, not "whatever's convenient to pass along."

By the time `get_analysis_summary` runs, the full `GET /me/analysis` result
is already sitting in memory -- charts, Best Fit, eligibility verdicts, the
works. It would have been easy to just hand the whole thing (or a large
slice of it) to the prompt-building code and let the prompt itself decide
what to mention.

## Decision

`app/services/ai_summary.py`'s `generate_summary(area_scores, group_scores)`
is the *entire* privacy boundary. Its two parameters are lists of
`{"name": str, "score": float}` -- interest-area names + scores, and
subject-group names + scores -- and nothing else. The caller
(`app/services/analysis.py`'s `get_analysis_summary`) builds those two lists
by hand from the already-computed analysis result, picking out only
`area`/`score` and `name`/`score` pairs.

Never passed in, by construction (there's no parameter for them): email,
race, citizenship, raw SPM grades (letters like `A+`), the student's user
id or name, program names, or eligibility verdicts/reasons. The system
prompt also explicitly tells GPT-5 it wasn't given any of that and must
never invent or assume it -- so even if a future edit accidentally passed
more data in, the model is instructed not to use extra context it wasn't
told to expect (defense in depth, not a substitute for the parameter
restriction itself).

## Reason

**The trade-off accepted:** the summary can only ever describe relative
subject/interest strengths in general terms -- it can never say something
like "given your Bumiputera status and citizenship, program X is a strong
match," even though that might read as more personalized or useful.

**Why this was accepted anyway:** PDPA 2010 and PRD T4 require collecting
only what's needed, and a third-party AI API is the highest-risk place to
apply that rule -- once a request leaves the process, the app has no more
control over it. Restricting the function signature itself (not just the
prompt wording) means a future contributor physically cannot regress this by
accident while extending the prompt; they'd have to deliberately add a new
parameter and thread new data through, which is a much more visible, more
reviewable change than editing a prompt string. This is also directly
testable: `backend/tests/test_ai_summary.py`'s
`test_ai_request_excludes_sensitive_fields` captures the *exact* outgoing
`kwargs` sent to the (mocked) OpenAI client and asserts none of the excluded
fields appear anywhere in them, including the system prompt text itself.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 6 section
      2 "Privacy boundary" and the Behavioral Constraints list both
      describe this and link here)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entry
      for `ai_summary.py` and the `/me/analysis/summary` route both point
      here)
- [ ] No upstream doc update needed
