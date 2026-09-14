# 0019 - The "excel" chart shows all 7 subject groups, with N/A for empty ones

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

PRD T1 says a subject group with no subjects taken is **hidden** on Chart 1, "not shown as 0". So a student's "What you're likely to excel in" chart had as many spokes as groups they took subjects in. For example, the product owner's test account showed only 4.

The product owner asked for all 7 groups to always show, with "N/A" for a group that has no value.

T1 also says "the required subjects always give at least 3 groups". That isn't true: Bahasa Melayu is in Languages and Sejarah is in Humanities, so the required subjects only guarantee **2**. A 2-spoke chart draws as a flat line, which is one more reason to show every group.

## Decision

**Display only. The backend is unchanged.**
- `GET /me/analysis` still returns only the groups the student took (T1). The Likely to excel list, Best Fit, the AI summary, the summary's "no SPM results yet" check, and the golden tests all keep using that list.
- `client/src/constants.js` gets `SUBJECT_GROUPS`, a copy of the backend's fixed list of 7 groups, in the same order `GET /me/analysis` uses (by code).
- `client/src/pages/MyResults.jsx` builds the chart's rows from all 7 groups. A group missing from the API gets `score: null`. If the API ever returns a group not in the list, it's still added.
- `client/src/components/RadarChartCard.jsx` treats `score: null` as "no value":
  - the spoke label says **N/A** in grey,
  - the web is drawn at the centre for that spoke, with no dot,
  - the tooltip says N/A,
  - the screen-reader table says "N/A, no subjects taken".
- With **no SPM results at all**, the chart still shows its "Add your SPM results" message, not 7 N/As.

## Reason

- Every student sees the same 7 spokes, so charts are easier to compare and never collapse into a flat line.
- "N/A" is honest: the student didn't score 0, they just didn't take a subject in that group.
- Keeping the backend as-is means no rule, test, cache or AI change. Mirroring a fixed list in `constants.js` follows the existing pattern for `SPM_GRADES`.

**Trade-off:** an N/A spoke pulls the web shape to the centre, which can look like a low score. The grey "N/A" label and the missing dot are what tell the two apart.

**Keep in sync:** if a subject group is ever added or renamed in `backend/app/importer/subjects.py`, update `SUBJECT_GROUPS` in `constants.js` too.

## Impact

- [x] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
