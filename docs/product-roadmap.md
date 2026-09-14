# Product Roadmap

> **Quick summary**
> - **What:** the build order for FurtherXpert, in 8 phases.
> - **Why this order:** each phase stands on the one before. First the base, then login, then data, then rules, then screens, then AI, then polish.
> - **Now:** Phases 1–7 are shipped, so the first release is fully built. **Phase 8 (UI redesign) is in progress:** the code is committed, but the logged-in pages still need a browser check.
> - **Where the details live:** `docs/prd/furtherxpert-prd.md`.

> **Type:** Roadmap | **Must stay current:** Yes -- update when phases, features, or priorities change

<!-- AI Context
Role: This is the top-level sequencing document for the entire product.
It defines development phases, maps PRDs to phases, and captures the
rationale for ordering. Use it to understand *what is being built when*
and *why that order was chosen*.

When a new PRD is created, register it here under the appropriate phase.
When a feature ships or a phase graduates, update the status columns.
When priorities shift, update phase assignments and record the reasoning
in the Prioritization Log below.

Individual PRDs hold feature-level detail. This document holds the
cross-feature ordering logic. Do not duplicate PRD content here.
Status values: draft / in-progress / shipped. Mark shipped only when the
phase's graduation criteria pass.
-->

## Product Vision

FurtherXpert helps every Malaysian SPM holder see what they're best at and what they love. It then shows the public-university courses they can really get into, checked against official rules.

## Phasing Strategy

- Phases follow **what each part relies on**. Login needs the base setup. The rules need data. The screens need the rules.
- A phase **graduates** (counts as finished) when its checks pass and the reviewer approves it.
- Each phase is built, tested, reviewed, and then its docs are updated before the next one starts.

## Phases

### Phase 1: Foundation

**Trigger:** PRD agreed (2026-09-12).
**Graduation criteria:** backend tests pass, the client build passes, and the Docker setup file is valid.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T8) | `docker-compose.yml`, `backend/`, `client/` | shipped | Confirmed live 2026-09-12: all 3 services start, `/health` reports `db: ok`, client loads |

### Phase 2: Accounts

**Trigger:** Phase 1 shipped.
**Graduation criteria:** acceptance check 4 passes (wrong password, expired login, no cross-user access). Delete account removes everything.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T3, T4) | `backend/app/api/`, `backend/app/services/` | shipped | Backend only. Sign up, log in, refresh, log out, view/delete account. No screens yet (client pages come in Phase 6) |

### Phase 3: Reference data

**Trigger:** Phase 2 shipped.
**Graduation criteria:** the sesi 2026/2027 snapshot loads through a migration. The program, subject and university lists answer correctly.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T2, T5) | `backend/app/importer/`, `backend/data/upu/`, `backend/migrations/` | shipped | Confirmed live 2026-09-12: sesi 2026/2027 loaded -- 20 universities, 166 category-A programs (11 of the 20 universities), 162 category-B rule sets, 328 `program_requirements` rows, 117 subjects, 9 interest areas. 100% fully parsed, both categories (no `unparsed` rows; `unverifiable` rows are interview notes only). 43 backend tests pass. Live-checked: `GET /subjects`, `/universities`, `/programs?area=...`, `/programs/UE4481001` all return 200 |

### Phase 4: Student input

**Trigger:** Phase 3 shipped.
**Graduation criteria:** a student can save SPM results and interest-test answers, and gets them back.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T1, T6) | `backend/app/api/`, `backend/app/models/` | shipped | Backend only. Confirmed live 2026-09-12: `PUT /me/results` and `PUT /me/interest-answers` reject bad grades, unknown subjects, and unknown question/option ids; a retake fully replaces old interest answers; a student can't read or write another student's data; deleting an account cascades to `spm_results` and `interest_answers`. 59 backend tests pass. No screens yet (client pages come in Phase 6) |

### Phase 5: Rules engine

**Trigger:** Phase 4 shipped.
**Graduation criteria:** acceptance checks 1–3 pass (golden tests, e-Panduan match, each subject counts once).

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T1, T2) | `backend/app/services/` | shipped | Confirmed live 2026-09-13: `GET /me/analysis` computes both charts (subject-group scores, interest-area scores), Best Fit, and eligibility, and caches the result in the new `analysis` table. 104 backend tests pass (up from 59), including golden tests for 6 sample students (`backend/tests/golden/`) -- Amir/Mei Ling share identical grades and answers but differ by race, proving a Bumiputera-only program (`UE4481001`) splits them (Amir Eligible, Mei Ling Not Eligible) while a non-Bumiputera-only equivalent (`UA4481001`) makes Mei Ling Eligible too; a counts-once trap (one subject can't satisfy two rule clauses); category A vs B by `spm_year`; cache invalidation on both `PUT /me/results` and `PUT /me/interest-answers`; cross-user isolation; and a non-citizen still gets full charts with an empty Best Fit. Live smoke test also passed: register, save results + answers, `GET /me/analysis` showed sane charts/Best Fit/reasons, `DELETE /me` cleaned up |

### Phase 6: Client pages

**Trigger:** Phase 5 shipped.
**Graduation criteria:** every page in T7 works end to end. Charts have text-table versions.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T7) | `client/src/` | shipped | Confirmed live 2026-09-13: all 8 pages built (Register, Login, SPM Results, Interest Test, My Results, Explore, Program Detail, Account) plus shared auth/nav/chart pieces. 116 backend tests pass (up from 104 -- new tests cover the interest-test partial-save and completeness-gate change, decision `0008`). `npm run build` passes. The full user journey (register through delete account, including saving results, answering the interest test partway, reloading to resume, finishing it, and seeing the analysis page change once complete) was checked at the API level and cross-checked against the page code; a manual look in a real browser is still recommended before wider rollout |

### Phase 7: AI summary

**Trigger:** Phase 6 shipped.
**Graduation criteria:** acceptance checks 5 and 7 pass (AI failure is safe, summary under 10 seconds).

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T4) | `backend/app/services/`, `client/src/` | shipped | Confirmed live 2026-09-14: a throwaway account got a real `GET /me/analysis/summary` reply from GPT-5 in ~6.0 seconds (acceptance criterion 7), well under the 10-second budget; the account was then deleted. 126 backend tests pass (up from 116), including a payload-privacy test (the outgoing OpenAI request carries no email/race/citizenship/grades/user id), a forced-AI-failure test showing charts still return via `/me/analysis` while the summary route returns a friendly `unavailable` state (acceptance criterion 5), a timeout-path test, cache-hit/cache-invalidation tests, and a cross-user isolation test. `ai_summary.py` sends only interest-area and subject-group names + scores to GPT-5, with a 6-second hard timeout and no retries. The live check found the prompt-only "120 words or fewer" instruction wasn't reliable on its own (one reply came back at 122 words), so deterministic code-level truncation (`_enforce_word_limit`) was added as the real guarantee -- see decision `0013`. `npm run build` passes |

### Phase 8: UI redesign

**Trigger:** Phase 7 shipped, and the product owner asked for a production-quality look (2026-09-14).
**Graduation criteria:** acceptance checks 1–10 in `docs/prd/ui-redesign-prd.md` pass, and every item in the Definition of Done in `docs/plan/ui-redesign-plan.md` is ticked. That includes the by-hand browser check of the logged-in pages.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/ui-redesign-prd.md` | `client/src/` | in-progress | Code committed 2026-09-14 (`9fe75b1`), client files only. Built before its PRD and plan, which were written afterwards (decision `0015`). New shared look (`components/ui.jsx`, `index.css`), sticky menu with a phone menu, footer, 404 page, every page rebuilt, program names in title case (decision `0016`), and spider charts that show scores at each spoke instead of scale numbers (decision `0017`). The "View as a table" toggle under each chart was then removed from view; the table stays for screen readers (decision `0018`). The "excel" chart now always shows all 7 subject groups, with N/A for groups with no subjects; display only, no backend change (decision `0019`). **Checked:** `npm run build` passes; lint shows no new warnings; Home, Log in, Register, Explore and Program Detail were checked in a browser at about 700px and 1200px wide; My Results, including both charts with real data, at about 700px wide (one bug fixed: eligibility pills stretched full width). **Still open:** a browser check of SPM Results, Interest Test and Account; My Results at laptop width; a 375px phone check; the 404 page; a keyboard walk-through; reviewer sign-off |

### Phase 9: Interest test rotation

**Trigger:** the product owner asked for a 300-question bank with 40-question sets and a rotate button, and agreed the PRD and plan (2026-09-14).
**Graduation criteria:** acceptance criteria 1–12 in `docs/prd/interest-test-rotation-prd.md` pass, and steps 9.1–9.4 in `docs/plan/interest-test-rotation-plan.md` are done.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/interest-test-rotation-prd.md` | `backend/data/`, `backend/app/`, `backend/migrations/`, `client/src/` | in-progress | PRD and plan agreed 2026-09-14. Built the same day, not yet committed. **Question bank:** 280 new questions (300 total), every area tagged 133 or 134 times. The product owner handed their review to the assistant (decision `0021`). **Backend:** per-student 40-question sets, `GET /me/interest-test`, `POST /me/interest-test/rotate`, scores from the latest finished set, public `GET /interest-test` removed (decision `0020`). **Page:** "N of 40", Get new questions with confirm, fresh-set note; Home says 40. **Checked:** 152 backend tests pass (up from 126), including golden numbers re-worked by hand; migrations applied to the dev database (300 questions); a live API run with a throwaway account (open, resume, rotate with no repeats, finish, new set keeps results, account deleted); `npm run build` passes; lint shows no new warnings. **Still open:** a by-hand browser check of the Interest Test page at phone and laptop width (needs the product owner to log in), and reviewer sign-off |

### Phase 10: Why this diploma

**Trigger:** the product owner asked for every suggested diploma to explain why it's suggested, and agreed the PRD and plan (2026-09-14).
**Graduation criteria:** acceptance criteria 1–10 in `docs/prd/result-explanations-prd.md` pass, and steps 10.1–10.3 in `docs/plan/result-explanations-plan.md` are done.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/result-explanations-prd.md` | `backend/app/services/`, `backend/app/schemas/`, `client/src/` | in-progress | PRD and plan agreed 2026-09-14. Built the same day, not yet committed. **Backend:** `eligibility.find_matching` (which grade met which rule, same backtracking as the checker), pure `services/explanations.py`, `why` on every Best Fit program, cache-clearing migration `c9e5a1b63d42` (decision `0022`). **Page:** closed-by-default "Why this diploma?" under each program (`WhyThisDiploma.jsx`). **Checked:** 171 backend tests pass (up from 152), including hand-written expected sentences, golden checks for Amir on `UE4481001` and Rahman on `UE4213001`, and an agreement test between `find_matching` and the checker over every real rule tree; golden chart and Best Fit numbers unchanged; a live API run with a throwaway account showed correct explanations on all 10 shown diplomas (account deleted); `npm run build` passes; lint shows no new warnings. **Still open:** a by-hand browser check of My Results at phone and laptop width (needs the product owner to log in), reviewer sign-off. **Found, not fixed here:** some UiTM diplomas are Bumiputera-only at program level but not in their rule data (separate task). Ranking diplomas by fit is listed under "Later" as its own phase |

## Cross-Cutting Concerns

| Concern | Introduced In | Matured In | Current State |
|---|---|---|---|
| Docker setup | Phase 1 | Phase 3 | Running live: db + backend + client |
| Login and access control (JWT) | Phase 2 | Phase 6 | Full stack done: the backend guards every account, student-input, and analysis route with a JWT (JSON Web Token, a signed login pass), scoped to the caller only. The client (`client/src/context/AuthContext.jsx`) keeps the access token in memory only (never saved to disk), refreshes it silently on page load, and retries a failed request once via refresh before sending the student to Login |
| Privacy (PDPA 2010) | Phase 2 | Phase 7 | Rules written in PRD T4. Confirmed live 2026-09-12: `DELETE /me` cascades to `spm_results` and `interest_answers` too, not just the account row. Phase 7 adds a second privacy boundary: `GET /me/analysis/summary` sends OpenAI only interest-area and subject-group names + scores -- never email, race, citizenship, raw grades, a user id, or program/eligibility data (decision `0010`), checked by an automated test that inspects the real outgoing request payload |
| Database migrations (Alembic) | Phase 1 | Phase 5 | 6 migrations: the `users` table, the reference-data tables, the sesi 2026/2027 data load, the student-input tables (`spm_results`, `interest_questions`, `interest_options`, `interest_answers`), the approved interest-test seed, and the new `analysis` cache table (one row per user, `ON DELETE CASCADE` to `users`). Both data migrations still replace their own rows on each re-run, leaving everything else untouched |
| Automated tests | Phase 1 | Phase 7 | 126 backend tests pass (health + accounts + importer + reference routes + student input + scoring + eligibility + analysis + golden student tests + the AI summary route), on a separate test database. Phase 6 added no new backend test file, but extended existing ones for the interest-test partial-save/completeness change (decision `0008`); Phase 7 added `backend/tests/test_ai_summary.py` (10 tests), which mocks the OpenAI client so no test makes a real network call. The client's checks so far are the `npm run build` pass and a manual API-level journey walk-through, not an automated test suite |
| Rules engine (scoring, eligibility, caching) | Phase 5 | Phase 5 | `backend/app/services/scoring.py` and `eligibility.py` are pure functions (no DB); `analysis.py` loads a student's data, calls them, and caches the result in `analysis`. `PUT /me/results` and `PUT /me/interest-answers` invalidate that cache unconditionally on every successful save, so `GET /me/analysis` never serves stale numbers |

## PRD Registry

| PRD | Phase | Module | Status |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (plan: `docs/plan/furtherxpert-plan.md`) | 1–7 | `backend/`, `client/` | shipped |
| `docs/prd/ui-redesign-prd.md` (plan: `docs/plan/ui-redesign-plan.md`) | 8 | `client/` | in-progress |
| `docs/prd/interest-test-rotation-prd.md` (plan: `docs/plan/interest-test-rotation-plan.md`) | 9 | `backend/`, `client/` | in-progress |
| `docs/prd/result-explanations-prd.md` (plan: `docs/plan/result-explanations-plan.md`) | 10 | `backend/`, `client/` | in-progress |

## Prioritization Log

| Date | Change | Reason |
|---|---|---|
| 2026-09-12 | Set the 7-phase order | Each phase relies on the one before it |
| 2026-09-12 | Added the implementation plan before Phase 3 | Phases 1–2 were built from the PRD alone; from Phase 3 on, builds follow the plan |
| 2026-09-14 | Added Phase 8, UI redesign | The product owner wanted a production-quality look before wider rollout. Its PRD and plan were written after the build (decision `0015`) |
| 2026-09-14 | Added Phase 9, Interest test rotation | Retakes showed the same 20 questions. The product owner wants a 300-question bank, 40-question sets, and a rotate button |

## Later (not in the first release)

- Rank Best Fit diplomas by how well they fit the student, instead of Eligible first then A to Z (the product owner agreed this should be its own phase, 2026-09-14)
- Admin editing screens
- Private universities
- Asasi, Matrikulasi and polytechnic routes
- Malay-language screens
- Student merit calculator
- Dark mode
- Privacy Policy and Terms pages

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/documentation-standard.md` | Standard | Governs how all docs are maintained |
| `docs/prd/furtherxpert-prd.md` | Intent (PRD) | What Phases 1–7 build, and why |
| `docs/plan/furtherxpert-plan.md` | Plan | How Phases 1–7 are built: tasks and checks |
| `docs/prd/ui-redesign-prd.md` | Intent (PRD) | What Phase 8 (UI redesign) builds, and why |
| `docs/plan/ui-redesign-plan.md` | Plan | How Phase 8 is built, with its Definition of Done |
| `docs/furtherxpert-workflow.md` | Workflow | How the app behaves today |
| `docs/reference/folder-structure.md` | Reference | Structural placement of modules |
| `docs/decisions/NNNN-*.md` | Decision log | Deviations that may affect roadmap |
