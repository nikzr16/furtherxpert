# 0012 - AI Summary Uses a 6-Second Hard Timeout and No Automatic Retries

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

PRD T7 acceptance criterion 7 requires "the AI summary loads in under 10
seconds, separately, so charts never wait for it." That 10-second figure is
a budget for the *whole* `GET /me/analysis/summary` request/response cycle
as measured by the client -- not just the time spent inside the OpenAI SDK
call. Network round trips, FastAPI request handling, and the DB read/write
around the AI call all eat into that same 10 seconds.

The OpenAI Python SDK supports both a configurable request timeout and
automatic retries on failure (`max_retries`, default 2 in the SDK). Left at
its defaults, a slow or flaky request could retry twice, each attempt
allowed to run close to whatever timeout was set, multiplying the worst-case
wait well past the 10-second budget.

## Decision

`app/services/ai_summary.py` creates the OpenAI client with
`timeout=REQUEST_TIMEOUT_SECONDS` (`6.0`) and `max_retries=0`. A request
that hasn't completed after 6 seconds is abandoned and raised as an
`AISummaryError`; it is never retried automatically.

## Reason

**The trade-off accepted:** a single slow-but-would-have-eventually-
succeeded OpenAI request is now treated as a hard failure (`status:
"unavailable"`) instead of being given a second chance via a retry, and the
student sees "Summary unavailable right now" a bit more often than they
would with retries enabled.

**Why this was accepted anyway:** 6 seconds leaves roughly 4 seconds of
headroom under the PRD's 10-second budget for everything else in the
request cycle (network, FastAPI, the DB read for the cached analysis and
the DB write for the new summary) -- deliberately generous headroom rather
than cutting it close. Turning off retries makes that 6-second figure an
actual ceiling on how long the AI portion of the request can take: with
retries on, the real worst case would be `(1 + max_retries) x timeout`,
which could blow the whole budget on its own before any of the surrounding
work even runs. A live check against the real OpenAI API (a throwaway
account, real `.env` key, one real `GET /me/analysis/summary` call)
measured ~6.0 seconds end to end for a 122-word reply -- comfortably under
10 seconds with this timeout in place, confirming the budget holds in
practice, not just on paper. Because
`get_analysis_summary` already turns any `AISummaryError` into a friendly
`unavailable` response rather than a `500` (PRD T7 acceptance criterion 5,
proj-auth-security skill Section 5), a slightly higher failure rate here is
cheap: the student always still gets their charts, and can just try again
later for the summary.

## Impact

- [x] Workflow doc updated (`docs/furtherxpert-workflow.md` Flow 6 section
      1 step 5, the Defaults table, and the Error States table all
      describe this and link here)
- [x] Reference doc updated (`docs/reference/folder-structure.md`'s entry
      for `ai_summary.py` points here)
- [ ] No upstream doc update needed
