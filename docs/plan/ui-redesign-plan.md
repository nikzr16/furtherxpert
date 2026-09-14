# FurtherXpert UI Redesign Implementation Plan

> **Quick summary**
> - **What:** how the Phase 8 UI redesign was built. The PRD (`docs/prd/ui-redesign-prd.md`) says *what* and *why*; this plan says *how*.
> - **Who uses it:** anyone finishing, reviewing or changing the Phase 8 pages.
> - **Now:** the code is committed (`9fe75b1`). Some checks are still open. See the **Definition of Done** below.
> - **If the build must differ from this plan:** don't edit the plan. Add a note in `docs/decisions/`.

> **Type:** Plan | **Must stay current:** No -- record divergences in decision log, rewrite only during re-planning

<!-- AI Context
Role: This document describes *how* the Phase 8 UI redesign is built, not *what*
or *why*. Read `docs/prd/ui-redesign-prd.md` first.
Written 2026-09-14, after the code was committed (decision 0015). The task list
records what was built. The Definition of Done marks each item done [x] or open
[ ], and says how each done item was checked. Keep that honest: only tick an
item when it was really checked that way.
Do not rewrite this document during coding. If the implementation diverges from
this plan, add an entry to the decision log instead.
-->

## Overview

Phase 8 changes **how the website looks**, not what it does. Every page keeps its data loading, its API calls, and its rules from Phase 6 and Phase 7. What changes is the layout, the styling, and a few small display helpers.

The work has 3 layers:
1. **Shared building blocks** that every page uses.
2. **The site frame** around every page: top menu, footer, 404 page.
3. **Each page**, rebuilt on top of those blocks.

## Technical Approach

1. **Build once, reuse everywhere.** Common styles live as classes in `client/src/index.css`, for example `.btn`, `.input`, `.card`. Common pieces live in `client/src/components/ui.jsx`, for example `PageHeader`, `Alert` and `Badge`. Pages use these instead of repeating long style lists.
2. **Looks only.** Each page's state, effects and API calls stay the same. Only the markup and styling change. The client still never works out a score.
3. **Phone first.** Styles start with the phone layout, then widen at Tailwind's **breakpoints** (screen widths where the layout changes: `sm` 640px, `md` 768px, `lg` 1024px, `xl` 1280px).
4. **Accessibility kept.** Real form inputs stay in the page, even when styled as tiles, so keyboards and screen readers still work. Each chart's `<table>` stays.
5. **No new libraries.** Icons are inline SVG drawings. The font is Poppins, from Google Fonts, with system fonts as a fallback.

## System Components

| Component | Responsibility |
|---|---|
| `client/src/index.css` | Tailwind theme (the Poppins font) and shared classes: `.container-page`, `.card`, `.btn` + variants, `.label`, `.input`, `.select`, `.hint`, `.field-error`, `.link`, `.bg-grid` |
| `client/src/components/ui.jsx` | `Icon`, `LogoMark`, `Logo`, `PageHeader`, `Alert`, `Badge`, `ProgramFlags`, `Spinner`, `PageLoader`, `PageError` |
| `client/src/components/Nav.jsx` | Sticky top menu. Links change when logged in. Folds into a menu button below 768px |
| `client/src/components/Footer.jsx` | Site footer with links and the e-Panduan data credit |
| `client/src/components/AuthShell.jsx` | Two-panel layout shared by Log in and Register |
| `client/src/components/RadarChartCard.jsx` | Chart card: custom spoke labels (name + score), hidden scale numbers, empty state, collapsible text table |
| `client/src/components/EligibilityBadge.jsx` | Splits into `VerdictPill` and `ReasonList`, so My Results can place them separately |
| `client/src/components/AISummaryCard.jsx` | Restyled summary card with a loading skeleton. Same independent fetch as Phase 7 |
| `client/src/App.jsx` | Page frame (menu, page, footer), `ScrollToTop`, and the `*` route to the 404 page |
| `client/src/pages/*.jsx` | Every page rebuilt with the shared pieces, plus the new `NotFound.jsx` |
| `client/src/programName.js` | `displayProgram()` now also title-cases names (decision `0016`) |
| `client/index.html`, `client/public/favicon.svg` | Page title, description, theme colour, and the new logo icon |

## Processing Flow

**A. How any page is drawn**
1. `App.jsx` draws the frame: `Nav` at the top, the page in the middle, `Footer` at the bottom.
2. On every address change, `ScrollToTop` jumps back to the top of the page.
3. A logged-in page goes through `ProtectedRoute` first. While login is still being checked, it shows `PageLoader`.
4. The page loads its data exactly as in Phase 6. While loading, it shows `PageLoader`. If loading fails, it shows `PageError`.
5. The page draws a `PageHeader` (small label, title, description, optional buttons), then its content in `.card` blocks.

**B. How a spider chart spoke label is drawn** (`RadarChartCard.jsx`)
1. Recharts gives each spoke's end point (`x`, `y`) and the chart centre (`cy`).
2. `splitLabel` splits a name longer than 12 characters at " & ". For example, "Healthcare & Social Services" becomes "Healthcare &" and "Social Services".
3. `SpokeLabel` draws the name lines in small grey text, and the score in bold, in the chart's colour, underneath.
4. Labels above the centre grow upward, labels below grow downward, and side labels are centred. So no label covers the web.
5. The 0–100 scale numbers are switched off (`PolarRadiusAxis tick={false}`).

## Dependencies

| Dependency | Purpose |
|---|---|
| Tailwind CSS v4 | All styling, including the shared classes and `has-*` variants for answer tiles |
| Recharts | Spider charts, including the custom spoke labels |
| React Router | Page routes, the active menu link, the 404 route |
| Google Fonts (Poppins) | The site font. Falls back to system fonts if it can't load |

No new packages were added.

## Implementation Phases

### Phase 8: UI redesign

**Goal:** every page shares one polished, responsive look, and the spider charts read cleanly. Behaviour doesn't change.

**PRD sections:** `docs/prd/ui-redesign-prd.md` sections 3, 5 and 6. Main PRD T7 (pages, accessibility table).

**Tasks (as built):**
1. **Look at every page first** in a browser, and list what looks unfinished.
2. **Shared styles:** add the theme and shared classes to `index.css`.
3. **Shared pieces:** create `components/ui.jsx` (icons, logo, page header, alerts, badges, loaders, error state).
4. **Site frame:** rebuild `Nav.jsx` (sticky, phone menu), add `Footer.jsx`, add `ScrollToTop` and the 404 route in `App.jsx`, add `pages/NotFound.jsx`, update `index.html` and the favicon.
5. **Log in and Register:** add `AuthShell.jsx`, rebuild both forms, and turn citizenship into a Yes/No toggle.
6. **Home:** headline section with a labelled example chart, live stats, how it works, features, closing banner.
7. **SPM Results:** table card, "Add a subject" row, a save bar with a "what's missing" hint, tips panel.
8. **Interest Test:** progress bar pinned under the menu, answer tiles, finished card.
9. **Spider chart fix:** custom spoke labels, hidden scale numbers, wider margins, text table starts closed (decision `0017`).
10. **My Results:** setup checklist, restyled AI summary card, chart cards, Best Fit cards using `VerdictPill` and `ReasonList`.
11. **Explore:** search and filter bar, card grid, "Clear filters", empty state.
12. **Program Detail:** fact tiles, Category A / B tabs, "No extra requirements" message, side panel.
13. **Account:** profile card, "Delete account" area. The 2-step delete stays.
14. **Program names:** title case in `programName.js`, after checking all 166 names contain no acronyms (decision `0016`).
15. **Build and lint:** `npm run build` and `npx oxlint src`.
16. **Browser check:** every page, at phone and laptop width.

**Check:** the PRD's acceptance criteria 1–10, tracked in the Definition of Done below.

### Definition of Done (Phase 8)

Also called: **DoD**, the list that must be fully ticked before the phase counts as finished.

**Code**
- [x] `npm run build` passes. *Checked 2026-09-14 by running it. Only warning: the main code file is over 500 kB.*
- [x] Lint shows no new warnings. *Checked 2026-09-14 with `npx oxlint src`: 3 warnings, all from code that existed before Phase 8 (`AuthContext.jsx` ×2, the loading reset in `ProgramDetail.jsx`).*
- [x] Only `client/` files changed. No backend, API or database change. *Checked in the file list of commit `9fe75b1`.*
- [x] Every page uses the shared pieces. *Checked by reading all 10 page files.*
- [x] Each chart still renders its text `<table>`. *Checked by reading `RadarChartCard.jsx`. Not yet seen in a browser.*
- [x] No untrue claims on the site. The Home chart says "Example result". *Checked by reading every page.*

**Checked in a real browser**
- [x] Home, Log in, Register, Explore and Program Detail look right at about 700px wide and at 1200px wide. *Checked 2026-09-14 in the in-app browser, with screenshots and page text.*
- [ ] The same public pages at a 375px phone width.
- [ ] SPM Results, Interest Test, My Results and Account, at phone and laptop width. *Not checked yet: needs a person to log in.*
- [ ] Spider chart labels with real data: no scale numbers, nothing cut off or overlapping, at phone and laptop width.
- [ ] Program names show in title case on My Results. *Seen on Explore and Program Detail; not yet on My Results.*
- [ ] The 404 page, by visiting an address that doesn't exist.
- [ ] Keyboard-only walk-through: Tab through each page, and the focus ring is always visible.

**Docs and review**
- [x] PRD, plan, roadmap entry, workflow doc, folder reference and decisions `0015`–`0017` written. *2026-09-14.*
- [ ] Reviewer checks the work against this plan and approves it.

## Testing Strategy

- **No automated client tests exist**, so Phase 8 relies on `npm run build`, the linter, and checks by hand in a browser.
- **Backend tests** don't need to re-run for Phase 8, because no backend file changed. They must still pass before any later phase.
- **By-hand browser checks** cover every page at 2 widths: 375px (phone) and 1200px or more (laptop). The logged-in pages need a real account with SPM results and a finished interest test, so the charts and Best Fit have data.
- **Say how each item was checked** (browser, code reading, or build) when ticking the Definition of Done.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Logged-in pages weren't browser-checked before commit | A layout bug may be live on My Results or the chart | Finish the open browser checks in the Definition of Done before calling Phase 8 shipped |
| A future yearly import adds a program name with an acronym, like "ICT" | It would show as "Ict" | Re-scan names for acronyms after each import (decision `0016`) |
| Google Fonts can't load (offline, or blocked) | The site falls back to system fonts | The fallback font list keeps it readable |
| Tailwind's `has-*` styles aren't supported in a very old browser | Answer tiles may not highlight when picked | The real radio input still works; modern browsers all support it |
| The main code file is over 500 kB | Slower first load on a slow phone connection | Split the code into smaller downloads in a later phase |

## Roadmap Phase

**Phase:** Phase 8, UI redesign, in `docs/product-roadmap.md`.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/product-roadmap.md` | Roadmap | Phase 8 status and graduation criteria |
| `docs/prd/ui-redesign-prd.md` | Intent | What this plan builds, and its acceptance criteria |
| `docs/prd/furtherxpert-prd.md` | Intent | Product rules the redesign must not change (T1–T8) |
| `docs/furtherxpert-workflow.md` | Workflow | How the pages behave today (Flow 5) |
| `docs/reference/folder-structure.md` | Reference | Where the client files live |
| `docs/decisions/0015-*.md` to `0017-*.md` | Decision log | Divergences from the normal process and from Phase 6 behaviour |

## Open Questions

- [ ] Who does the by-hand browser check of the logged-in pages, and when?
- [ ] Split the website code into smaller downloads in a later phase?
