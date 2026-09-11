# Product Roadmap

> **Quick summary**
> - **What:** the build order for SambungBelajarmu.ai v2, in 7 phases.
> - **Why this order:** each phase stands on the one before. First the base, then login, then data, then rules, then screens, then AI.
> - **Now:** Phase 1 (foundation) is shipped. Phase 2 (accounts) is next.
> - **Where the details live:** `docs/prd/sambungbelajarmu-v2-prd.md`.

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

SambungBelajarmu.ai helps every Malaysian SPM holder see what they're best at and what they love. It then shows the public-university courses they can really get into, checked against official rules.

## Phasing Strategy

- Phases follow **what each part relies on**. Login needs the base setup. The rules need data. The screens need the rules.
- A phase **graduates** (counts as finished) when its checks pass and the reviewer approves it.
- Each phase is built, tested, reviewed, and then its docs are updated before the next one starts.

## Phases

### Phase 1: Foundation

**Trigger:** PRD v2 agreed (2026-09-12).
**Graduation criteria:** backend tests pass, the client build passes, and the Docker setup file is valid.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T8) | `docker-compose.yml`, `backend/`, `client/` | shipped | `docker compose up` not yet run live, because the Docker engine was off |

### Phase 2: Accounts

**Trigger:** Phase 1 shipped.
**Graduation criteria:** acceptance check 4 passes (wrong password, expired login, no cross-user access). Delete account removes everything.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T3, T4) | `backend/app/api/`, `backend/app/services/` | draft | Features: sign up / log in, delete account |

### Phase 3: Reference data

**Trigger:** Phase 2 shipped.
**Graduation criteria:** the sesi 2026/2027 snapshot loads through a migration. The program, subject and university lists answer correctly.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T2, T5) | `backend/app/importer/`, `backend/data/upu/`, `backend/migrations/` | draft | e-Panduan importer + data migration |

### Phase 4: Student input

**Trigger:** Phase 3 shipped.
**Graduation criteria:** a student can save SPM results and interest-test answers, and gets them back.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T1, T6) | `backend/app/api/`, `backend/app/models/` | draft | Features: SPM results, interest test |

### Phase 5: Rules engine

**Trigger:** Phase 4 shipped.
**Graduation criteria:** acceptance checks 1–3 pass (golden tests, e-Panduan match, each subject counts once).

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T1, T2) | `backend/app/services/` | draft | Charts' numbers, Best Fit, eligibility |

### Phase 6: Client pages

**Trigger:** Phase 5 shipped.
**Graduation criteria:** every page in T7 works end to end. Charts have text-table versions.

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T7) | `client/src/` | draft | All screens, including Explore |

### Phase 7: AI summary

**Trigger:** Phase 6 shipped.
**Graduation criteria:** acceptance checks 5 and 7 pass (AI failure is safe, summary under 10 seconds).

| PRD | Module | Status | Notes |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` (T4) | `backend/app/services/`, `client/src/` | draft | GPT-5 gets scores only |

## Cross-Cutting Concerns

| Concern | Introduced In | Matured In | Current State |
|---|---|---|---|
| Docker setup | Phase 1 | Phase 3 | Config file valid; not yet run live |
| Login and access control (JWT) | Phase 2 | Phase 4 | Not started |
| Privacy (PDPA 2010) | Phase 2 | Phase 7 | Rules written in PRD T4 |
| Database migrations (Alembic) | Phase 1 | Phase 3 | Set up, no tables yet |
| Automated tests | Phase 1 | Phase 5 | Health check tests pass |

## PRD Registry

| PRD | Phase | Module | Status |
|---|---|---|---|
| `docs/prd/sambungbelajarmu-v2-prd.md` | 1–7 | `backend/`, `client/` | in-progress |

## Prioritization Log

| Date | Change | Reason |
|---|---|---|
| 2026-09-12 | Set the 7-phase order | Each phase relies on the one before it |

## Later (not in v2)

- Admin editing screens
- Private universities
- Asasi, Matrikulasi and polytechnic routes
- Malay-language screens
- Student merit calculator

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/documentation-standard.md` | Standard | Governs how all docs are maintained |
| `docs/prd/sambungbelajarmu-v2-prd.md` | Intent (PRD) | What each phase builds, and why |
| `docs/reference/folder-structure.md` | Reference | Structural placement of modules |
| `docs/decisions/NNNN-*.md` | Decision log | Deviations that may affect roadmap |
