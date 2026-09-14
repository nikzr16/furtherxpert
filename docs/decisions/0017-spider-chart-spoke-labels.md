# 0017 - Spider charts show scores at each spoke, not scale numbers

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

In Phase 6, `RadarChartCard.jsx` drew Recharts' default **scale numbers** (0, 20, 40, 60, 80, 100) at an angle across each chart. The area names used the default size. With 9 spokes and long names like "Healthcare & Social Services", the numbers and names crowded each other. The product owner said the chart looked broken.

Also, the chart's text table sat inside a `<details>` element marked `open`, so it always showed. The component's own comment and the workflow doc both described it as **collapsed by default**.

## Decision

In `client/src/components/RadarChartCard.jsx`:
- **Hide the scale numbers** (`PolarRadiusAxis tick={false}`, no axis line).
- **Custom spoke label** (`SpokeLabel`): the area name in small grey text, with its score in bold in the chart's colour underneath. For example "Sciences" with "78%" below it.
- **Long names split onto 2 lines** at " & " when longer than 12 characters.
- **Labels grow away from the chart:** labels above the centre grow up, labels below grow down, side labels are centred.
- **Wider chart margins**, so side labels aren't cut off.
- **The text table starts closed** (no `open`), matching the comment and the workflow doc. It's still in the page, so screen readers and keyboards still reach it (main PRD T7).

## Reason

- Students need each area's score, not the scale. Once every score is printed at its spoke, the scale numbers add nothing but clutter.
- The table is still one click away, and always available to screen readers.

**Not yet checked:** these labels haven't been seen with a real student's data in a browser. That check is an open item in the Definition of Done in `docs/plan/ui-redesign-plan.md`.

## Impact

- [x] Workflow doc updated
- [x] Reference doc updated
- [ ] No upstream doc update needed
