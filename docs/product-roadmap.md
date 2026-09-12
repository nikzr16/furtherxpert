# Product Roadmap

> **Quick summary**
> - **What:** the build order for FurtherXpert, in 7 phases.
> - **Why this order:** each phase stands on the one before. First the base, then login, then data, then rules, then screens, then AI.
> - **Now:** Phase 1 (foundation), Phase 2 (accounts, backend only), Phase 3 (reference data), and Phase 4 (student input, backend only) are shipped. Phase 5 (rules engine) is next.
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
| `docs/prd/furtherxpert-prd.md` (T1, T2) | `backend/app/services/` | draft | Charts' numbers, Best Fit, eligibility |

### Phase 6: Client pages

**Trigger:** Phase 5 shipped.
**Graduation criteria:** every page in T7 works end to end. Charts have text-table versions.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T7) | `client/src/` | draft | All screens, including Explore |

### Phase 7: AI summary

**Trigger:** Phase 6 shipped.
**Graduation criteria:** acceptance checks 5 and 7 pass (AI failure is safe, summary under 10 seconds).

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (T4) | `backend/app/services/`, `client/src/` | draft | GPT-5 gets scores only |

## Cross-Cutting Concerns

| Concern | Introduced In | Matured In | Current State |
|---|---|---|---|
| Docker setup | Phase 1 | Phase 3 | Running live: db + backend + client |
| Login and access control (JWT) | Phase 2 | Phase 4 | Backend done: sign up, log in, refresh, log out, view/delete account, plus the new `/me/results` and `/me/interest-answers` routes, all guarded by JWT (JSON Web Token, a signed login pass) and scoped to the caller only. No client screens yet |
| Privacy (PDPA 2010) | Phase 2 | Phase 7 | Rules written in PRD T4. Confirmed live 2026-09-12: `DELETE /me` cascades to `spm_results` and `interest_answers` too, not just the account row |
| Database migrations (Alembic) | Phase 1 | Phase 4 | 5 migrations: the `users` table, the reference-data tables, the sesi 2026/2027 data load, the student-input tables (`spm_results`, `interest_questions`, `interest_options`, `interest_answers`), and the approved interest-test seed. Both data migrations replace their own rows on each re-run, leaving everything else untouched |
| Automated tests | Phase 1 | Phase 5 | 59 tests pass (health + accounts + importer + reference routes + student input), on a separate test database |

## PRD Registry

| PRD | Phase | Module | Status |
|---|---|---|---|
| `docs/prd/furtherxpert-prd.md` (plan: `docs/plan/furtherxpert-plan.md`) | 1–7 | `backend/`, `client/` | in-progress |

## Prioritization Log

| Date | Change | Reason |
|---|---|---|
| 2026-09-12 | Set the 7-phase order | Each phase relies on the one before it |
| 2026-09-12 | Added the implementation plan before Phase 3 | Phases 1–2 were built from the PRD alone; from Phase 3 on, builds follow the plan |

## Later (not in the first release)

- Admin editing screens
- Private universities
- Asasi, Matrikulasi and polytechnic routes
- Malay-language screens
- Student merit calculator

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/documentation-standard.md` | Standard | Governs how all docs are maintained |
| `docs/prd/furtherxpert-prd.md` | Intent (PRD) | What each phase builds, and why |
| `docs/plan/furtherxpert-plan.md` | Plan | How each phase is built: tasks and checks |
| `docs/furtherxpert-workflow.md` | Workflow | How the app behaves today |
| `docs/reference/folder-structure.md` | Reference | Structural placement of modules |
| `docs/decisions/NNNN-*.md` | Decision log | Deviations that may affect roadmap |
