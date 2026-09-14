# 0018 - Chart text tables are hidden from view, kept for screen readers

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

After decision `0017`, each spider chart on My Results had a "View as a table" toggle under it. The product owner saw it in the browser and asked to remove it from both charts "for now".

Main PRD T7 still requires each chart to have a text-table version for screen readers (WCAG AA). So the table can't simply be deleted.

## Decision

In `client/src/components/RadarChartCard.jsx`:
- Remove the "View as a table" toggle (the `<details>` / `<summary>`) from both charts.
- Keep the same `<table>` (caption, Area, score) in the page, but **visually hidden** with Tailwind's `sr-only` class. Screen readers still read it. It's never `display: none`, which would hide it from screen readers too.
- Remove the small score bars that only the visible table used.

This also answers the open question in `docs/prd/ui-redesign-prd.md` section 8 ("should the table start open?"): it isn't shown at all for now.

## Reason

- The spoke labels already print every area's score next to its name (decision `0017`), so sighted students don't lose any information.
- Keeping the table for screen readers still meets PRD T7.
- **Trade-off:** a sighted student who finds the chart hard to read no longer has a table to open. Bring the toggle back if students ask for it.

## Impact

- [x] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
