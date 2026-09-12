# 0009 - Clean e-Panduan markers out of program names

> **Date:** 2026-09-13 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

Program names copied from e-Panduan carry 2 markers:
- **`#`** at the end of 32 names, for example "DIPLOMA ANIMASI #".
- **`Baru`** in 14 names, for example "DIPLOMA E-COMMERCE Baru". "Baru" is Malay for "new".

e-Panduan shows **no legend** explaining either marker. Shown raw, they confuse students.

## Decision

- The client shows program names **without** the markers.
- "Baru" becomes a **"New"** badge on Explore.
- `#` is hidden, because the data shows it only repeats the interview flag: **all 32** `#` programs require an interview, and **none** of the other 134 do. The "Interview required" badge already shows this.
- The raw names stay unchanged in the snapshot, the database and the API. Search still matches the raw name.
- Program Detail now shows the API's source credit: "Source: e-Panduan UPU, KPT, sesi 2026/2027" (PRD T5).

The cleanup lives in one helper, `client/src/programName.js`.

## Reason

- The meaning of `#` came from the data (32 of 32 versus 0 of 134), not from a guess.
- Keeping raw names in the data means a future import never loses information. Only the display changes.
- One helper keeps Explore, Program Detail and My Results consistent.

## Impact

- [ ] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
