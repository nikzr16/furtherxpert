# FurtherXpert UI Redesign

> **What kind of doc is this?** A product brief, also called a **PRD** (Product Requirements Document). It says **what** we're building and **why**. It does not say how.
>
> **Keep it updated?** No. If plans change while building, don't edit this doc. Add a note to the decision log (`docs/decisions/`) instead.

<!-- AI Context
Role: This doc captures what the Phase 8 UI redesign should do and why. For how
it was built, read `docs/plan/ui-redesign-plan.md`.
Reader: a layman. Follow `docs/layman-guide.md`.
Written 2026-09-14, AFTER the code was committed (commit 9fe75b1). See decision
0015 for why. It records what was actually built, not an earlier intent.
It layers on top of `docs/prd/furtherxpert-prd.md`, which still owns every
product rule (T1–T8). This PRD changes looks only.
Do not rewrite this doc during coding. If the build drifts from what's written
here, add a decision log entry instead.
-->

## Quick summary

- **What:** a new look for every page of the FurtherXpert website, so it looks like a finished product instead of a prototype.
- **Why:** the Phase 6 pages worked, but looked plain and unfinished. The spider chart's numbers crowded the chart and made it look broken.
- **For who:** SPM leavers using the site, on a phone or a laptop.
- **Done when:** every page shares one look, fits a phone and a laptop, and the spider charts read cleanly. How scores and eligibility work doesn't change.
- **Status:** Building. Code committed 2026-09-14 (commit `9fe75b1`). The logged-in pages still need a check in a real browser. This doc was written after the build (decision `0015`).

---

## 1. What problem are we solving?

The first version of the website used plain default styling: black text, thin grey borders, and no real page layout. Program names showed in ALL CAPS. On the spider chart, the scale numbers (20, 40, 60, 80, 100) sat at an angle across the web, so it looked broken.

A student deciding their future won't trust a site that looks half-built.

> **Example:** Aina opens My Results on her phone. She sees scale numbers stacked across the chart, and names like "DIPLOMA ANALISIS PELABURAN" in capitals. She can't tell which score belongs to which area.

## 2. Who is this for?

Also called: **user stories**.

1. **An SPM leaver** wants the site to **look professional and trustworthy** so they can **believe the results it gives them**.
2. **A student on a phone** wants **every page to fit their screen** so they can **use the site without zooming or scrolling sideways**.
3. **A student reading their charts** wants **each area's score shown next to its name** so they can **read the chart at a glance**.
4. **A student using a screen reader** wants **the text table of each chart to stay** so they **get the same information** (main PRD T7).

## 3. What we're building

Also called: **scope**.

- **One shared look** (a **design system**, meaning one set of reusable styles and pieces): colours, the Poppins font, buttons, form fields, cards, badges, alert boxes, loading and error states, icons, and a logo.
- **Site frame:** a top menu that stays visible while scrolling (it folds into a menu button on phones), a footer, a jump to the top of each new page, and a "Page not found" page.
- **Home page:** a headline section, an example chart clearly labelled "Example result", live counts of programs and universities, "How it works" steps, a features section, and a closing sign-up banner.
- **Log in and Register:** a form card, with a coloured brand panel beside it on wide screens. Citizenship becomes a Yes/No toggle.
- **SPM Results:** subjects in a clean table card, an "Add a subject" row, a save bar that says what's still missing, and a tips panel.
- **Interest Test:** a progress bar pinned under the top menu, answer options as clickable tiles, and a "You've answered every question" card.
- **My Results:** a "finish setting up" checklist, the AI summary card, the two chart cards, and Best Fit area cards.
- **Spider chart fix:** hide the scale numbers. Show each area's name with its score under it. Split long names onto 2 lines. Start the text table closed.
- **Explore:** one bar for search and filters, programs as cards, a "Clear filters" button, and a "no programs match" message.
- **Program Detail:** key facts in tiles, Category A / B tabs for entry rules, a "No extra requirements" message instead of an empty box, and a side panel for campuses and career paths.
- **Account:** a profile card and a clearly marked "Delete account" area.
- **Program names** shown in normal title case, for example "Diploma Analisis Pelaburan".

## 4. What we're NOT building (on purpose)

Also called: **non-goals** or **out of scope**.

- **Dark mode**, because one well-made light theme comes first.
- **Any change to scoring, eligibility, the API or the database**, because this phase is about looks only.
- **Malay-language screens**, because the main PRD already leaves them out.
- **Privacy Policy or Terms pages**, because there's no agreed wording for them yet.
- **Automated screen tests**, because the client has no test suite yet. Checks are done by hand.
- **Splitting the website code into smaller downloads**, because it doesn't change how pages look. The build warns the main file is over 500 kB; that can be handled later.

> **Why this matters:** writing this down stops the project from quietly growing bigger than planned.

## 5. How we'll know it's done

Also called: **acceptance criteria**.

| # | It's done when... | How we check |
|---|---|---|
| 1 | `npm run build` passes | Run it |
| 2 | No backend files change, and the client still never works out scores itself | Check the commit's file list, read the code |
| 3 | Every page uses the shared pieces. No page is left in the old plain style | Read the code, look in a browser |
| 4 | Every page fits a 375px-wide phone screen with no sideways scrolling | Try it by hand in a browser |
| 5 | Every page looks right on a laptop screen (1200px wide or more) | Try it by hand in a browser |
| 6 | Spider charts show no scale numbers. Each spoke shows a name and score. No label is cut off or overlapping, on phone or laptop | Try it by hand on My Results, with real data |
| 7 | Each chart still has its text table | Read the code, open it in a browser |
| 8 | A keyboard user can always see which button, link, field or answer tile is selected | Try it by hand with the Tab key |
| 9 | Program names show in title case. The raw names in the data and in search are unchanged | Look in a browser, read the code |
| 10 | Nothing on the site claims something untrue. The Home chart is labelled as an example | Read every page |

## 6. Rules and limits

Also called: **constraints**.

- **Looks only.** Pages make the same API calls, in the same way, as in Phase 6.
- **Rules stay in the backend.** The client never recalculates a score or eligibility (main PRD, plan "Technical Approach" 4).
- **No new libraries.** Use what the project already has: React, React Router, Tailwind CSS v4 and Recharts.
- **Keep accessibility.** Each chart keeps its text-table version (main PRD T7, WCAG AA).
- **Don't touch** the old SambungBelajarmu folders `sambungbelajarai/` and `archieve-sambung/`.

## 7. Decisions already made

| Decision | Why we chose it |
|---|---|
| Build our own small set of shared pieces (`components/ui.jsx` + style classes in `index.css`), not a UI library | No new library to install or learn, and it stays small |
| Indigo as the main colour, rose for the "likely to love" chart | The two charts look different at a glance, and both colours are easy to read |
| Icons are small inline drawings in code, not an icon package | No new library needed |
| Chart shows scores at each spoke instead of scale numbers | Students need each area's score, not the scale (decision `0017`) |
| Program names in title case | ALL CAPS is hard to read (decision `0016`) |
| The Home chart uses made-up numbers, labelled "Example result" | Shows what students get, without pretending to be anyone's real result |
| Home page counts come from the live API | The numbers stay true after each yearly data import |

## 8. Questions we still need to answer

- [ ] Does the site need a Privacy Policy or Terms page before launch, under PDPA? Product owner to decide.
- [ ] Should the site get a dark mode later?
- [ ] Should "View as a table" under each chart start open instead of closed? (decision `0017`)

---

## Words to know

| Word | What it means here |
|---|---|
| Design system | One set of shared styles and building blocks (buttons, cards, colours) that every page reuses |
| Responsive | The page rearranges itself to fit the screen, for example 1 column on a phone and 2 on a laptop |
| Sticky | Stays pinned at the top of the screen while you scroll |
| Spoke | One line of the spider chart, from the centre out to one area |
| Scale numbers | The 0–100 marks along a chart's spoke |
| Focus ring | The outline that shows which item the keyboard has selected |
| Title case | Capital first letter on each main word: "Diploma Seni Reka" |
| 404 page | The "Page not found" page shown for an address that doesn't exist |
| WCAG AA | Web Content Accessibility Guidelines, level AA, a common accessibility standard |

## Where this fits

**Roadmap phase:** Phase 8, UI redesign, in `docs/product-roadmap.md`.

| Related doc | What it tells you |
|---|---|
| `docs/product-roadmap.md` | Where Phase 8 sits, and its status |
| `docs/plan/ui-redesign-plan.md` | How it was built, and its Definition of Done |
| `docs/prd/furtherxpert-prd.md` | The product rules this redesign must not change (T1–T8) |
| `docs/furtherxpert-workflow.md` | How the pages behave today (Flow 5) |
| `docs/reference/folder-structure.md` | Where the client files live |
| `docs/decisions/0015-*.md`, `0016-*.md`, `0017-*.md` | Why the docs came after the code, the title-case names, and the chart labels |
