# 0016 - Program names are shown in title case

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

e-Panduan writes every program name in ALL CAPS, for example "DIPLOMA ANALISIS PELABURAN". Decision `0009` already cleans the "#" and "Baru" markers out of the name students see, but kept the capitals.

In the Phase 8 redesign, the capital names looked like shouting and were hard to scan in lists.

## Decision

`displayProgram()` in `client/src/programName.js` now also turns the name into **title case**:
- Each word gets a capital first letter, including the letter after "(", "-" or "/".
- Malay joining words stay lowercase, unless they start the name: `dan`, `di`, `untuk`, `dengan`, `dalam`, `serta`, `atau`, `bagi`, `ke`.

Example: "DIPLOMA AL QURAN & AS SUNNAH" shows as "Diploma Al Quran & As Sunnah".

The raw capital name is **unchanged** in the database, the API, and Explore's search.

**Checked first:** on 2026-09-14, all 166 program names from `GET /programs` (sesi 2026/2027) were scanned. None contains an **acronym** (a short word said letter by letter, like "ICT"). Every short word is a normal Malay word, like "DAN", "SENI" or "TANI". So title case can't wrongly lowercase an acronym in today's data.

## Reason

- Mixed case is faster to read than ALL CAPS.
- It's display-only, so no data, search or rule changes.
- It stays in the same helper as decision `0009`, so there's one place that decides how a name is shown.

**Risk:** a future yearly import could add a name with an acronym, like "ICT". It would show as "Ict". Re-run the acronym scan after each import, and add an acronym list to `programName.js` if one appears.

## Impact

- [x] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
