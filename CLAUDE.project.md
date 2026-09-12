# Project Context

This file is the project-specific context layer for this repository.

The reusable harness policy lives in `CLAUDE.md`; keep this file focused on the
actual product, codebase, team conventions, and commands for the project created
from the harness.

When guidance conflicts:
- Project behavior, domain rules, architecture, and commands in this file take
  precedence for project work.
- Harness routing, capability placement, and validation rules in `CLAUDE.md`
  still apply.

## Project Overview

**FurtherXpert** helps Malaysian SPM holders see what they will
**likely excel in** (from SPM grades) and **likely love most** (from a
20-question interest test), shown as two spider charts, plus the **UA diploma
programs** they qualify for under official **UPU** rules (syarat am + syarat khas).

The single source of truth for behaviour is `docs/prd/furtherxpert-prd.md`
(exact rules in its "Technical details" sections T1–T8). FurtherXpert is a full
revamp of the old SambungBelajarmu app: never reason from that old code or
PRD, and don't write about why its features were dropped.

## Tech Stack

- **Frontend (`client/`):** React (Vite), Tailwind CSS v4 (`@tailwindcss/vite`), Recharts, React Router.
- **Backend (`backend/`):** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, PyJWT, argon2.
- **Storage:** PostgreSQL 16 (Docker). Schema **and reference data** via Alembic migrations.
- **AI:** OpenAI `gpt-5` — writes the plain-words chart summary only.
- **Packaging:** `uv` (`backend/pyproject.toml` + `uv.lock`); npm (`client/package-lock.json`).
- **Deployment:** Docker Compose (`docker-compose.yml` at repo root: `db`, `backend`, `client`).

## Repository Layout

- **`backend/`**: FastAPI app, Alembic migrations, UPU snapshot data (`backend/data/upu/`), pytest suite.
- **`client/`**: React app.
- **`docs/`**: docs-first source of truth. Follow `docs/documentation-standard.md`,
  use `docs/templates/`, and write per `docs/layman-guide.md`.
  - `docs/prd/furtherxpert-prd.md`: the PRD (what and why).
  - `docs/plan/furtherxpert-plan.md`: the plan (how). **Builds follow it.**
  - `docs/furtherxpert-workflow.md`: how the app behaves today.
  - `docs/product-roadmap.md`: phase order and status.
  - `docs/project-knowledge.md`: background knowledge (starter).
  - `docs/reference/folder-structure.md`: structure reference.
  - `docs/decisions/`: decision log.
  - `docs/draft/` is the user's scratch space. Never read it unless explicitly referenced.
- **`sambungbelajarai/`, `archieve-sambung/`**: the previous SambungBelajarmu app. **Read-only reference. Never edit, never import from.**

## Commands

| Purpose | Command | Notes |
|---------|---------|-------|
| Start everything | `docker compose up --build` | db + backend + client |
| Migrate + load data | `docker compose exec backend uv run alembic upgrade head` | also runs on backend start |
| New migration | `docker compose exec backend uv run alembic revision --autogenerate -m "<msg>"` | review before commit |
| Backend tests | `docker compose exec backend uv run pytest` | or `cd backend && uv run pytest` |
| Backend deps | `cd backend && uv add <pkg>` | never pip install |
| Client dev | `cd client && npm run dev` | |
| Client build | `cd client && npm run build` | must pass |
| UPU import | `cd backend && uv run python -m app.importer.epanduan --session 2026/2027` | writes snapshot JSON |

## Code Conventions

1. **Docs-first:** before feature work, read `docs/product-roadmap.md`, then the phase's
   section in `docs/plan/furtherxpert-plan.md` (build from it), then the PRD sections it
   cites. Never edit the PRD or plan during coding; log divergences in `docs/decisions/`.
   Follow `docs/documentation-standard.md` for doc maintenance and the session-close checklist.
2. **Rules live in the backend.** Scoring and UPU eligibility are pure Python
   functions (no DB or HTTP inside), so they are unit-testable. The client only
   displays results; it never recomputes scores.
3. Backend layout: `app/api/` (routers), `app/models/` (SQLAlchemy),
   `app/schemas/` (Pydantic), `app/services/` (scoring, eligibility, auth, AI),
   `app/core/` (config, db, security).
4. Type hints everywhere in Python; functional components + hooks in React.
5. Before the rules or the auth code change, follow the matching project skill:
   - `.claude/skills/proj-furtherxpert-rules/SKILL.md`: scoring, UPU and data.
   - `.claude/skills/proj-auth-security/SKILL.md`: login and privacy.

## Coding Principles (Karpathy guidelines)

Adapted from [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
(MIT). Applies to every agent that writes or edits code. These rules trade some
speed for fewer mistakes; for Trivial-tier edits, use judgment.

**They add to the harness, never override it.** Routing, tiers, gates, retry
limits, skills, and the layman reply style in `CLAUDE.md` still win. If a
principle below seems to conflict with them, follow the harness.

1. **Think before coding.**
   - Say your assumptions out loud instead of silently guessing (in a
     Requirement Brief, tag them `[ASM]`).
   - If a request can mean two things, name both. Ask only when the choice
     really matters (the harness "genuine decision points" rule); otherwise
     pick the likely one, say so, and go.
   - If a simpler or safer approach exists, say so before building.
   - If something is unclear: read the relevant file first. Ask only if that
     doesn't answer it, and batch all questions into one round. Never invent.
   - Questions and assumptions shown to the user follow the layman style
     (numbered, one line each).
2. **Simplicity first.**
   - Build only what was asked. No "might need it later" features.
   - No abstractions (helpers, layers, config) for a single use.
   - Handle real failure and edge cases (the "execute" playbook requires it),
     but don't add guards for cases that truly can't happen.
   - Test: would a senior engineer call this overcomplicated? If 200 lines
     could be 50, rewrite it.
3. **Surgical changes.**
   - Touch only what the task needs. Don't reformat, rename, or "improve"
     nearby code.
   - Don't refactor code that already works.
   - Match the existing style, even if you'd write it differently.
   - Clean up only what *your* change made unused. Mention other dead code;
     don't delete it.
4. **Goal-driven execution.**
   - Turn the task into a check you can verify. Example: "fix the login bug"
     → "write a test that fails on the bug, then make it pass."
   - For multi-step work, write a short plan where each step has its own
     check. Keep it in your working notes (or the ad-hoc scratch path) —
     never rewrite existing PRDs/plans in `docs/`.
   - Loop until the checks pass, within the workflow's retry limit. Still
     failing after that? Stop and report — don't stop at "should work."

**Working if:** diffs contain only requested changes, fewer rewrites caused
by overbuilding, and questions come *before* mistakes, not after.

## Domain Rules

Full detail: `docs/prd/furtherxpert-prd.md` T1–T4 and the `proj-furtherxpert-rules` skill.

1. **Scope:** UA diploma programs only, UPU categories A (latest SPM) and B (older SPM).
2. **Grade points:** A+ 9, A 8, A- 7, B+ 6, B 5, C+ 4, C 3, D 2, E 1, G 0. There are no B-, C-, or F grades in SPM.
3. **Charts are deterministic code, never AI.** The same inputs always give the same numbers.
4. **Subject groups:** hide groups the student didn't take; never show them as 0.
5. **Interest scores:** normalise by the maximum possible picks per area. Each tag belongs to exactly one area.
6. **Eligibility labels:** only Eligible / Conditional / Not Eligible, always with reasons.
7. **Each SPM subject counts once** across syarat am and syarat khas.
8. **Hard stops:**
   - A non-citizen is Not Eligible for everything.
   - A non-Bumiputera student is Not Eligible for Bumiputera-only programs.
   - UPU's Bumiputera = Melayu, Anak Negeri Sabah, Anak Negeri Sarawak, Orang Asli.
9. **Conditional:** interview/test, or any rule grades can't check (medical, colour-blindness, age).
10. **Syarat khas is stored per program AND per category** (B includes older-syllabus subjects).
11. **Reference data** comes only from e-Panduan UPU snapshots, loaded by Alembic data migrations.
    - A new session **replaces** the old one, including admin edits.
    - Credit the source in the UI.
12. **Privacy (PDPA 2010):**
    - Race is used only for the Bumiputera check.
    - GPT-5 gets scores only.
    - Never log grades, answers, race, tokens, or AI replies.
    - Deleting an account deletes everything.

## Environment And Secrets

- The repo root `.env` is read by Docker Compose. Its template is `.env.example`, which is committed with no real values.
- Variables: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
  `JWT_SECRET`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `OPENAI_API_KEY`,
  `OPENAI_MODEL`, `FRONTEND_ORIGIN`.
- Never print, log, or commit `.env` values.

## Testing And Definition Of Done

- Touched backend code: `uv run pytest` passes. Touched client code: `npm run build` passes.
- Scoring or UPU changes must keep the **golden tests** passing (`backend/tests/golden/`).
  - Only update expected values when the rule change is intended, and say so.
- Treat tests as part of implementation, not a follow-up task.
- Never rewrite `docs/prd/furtherxpert-prd.md` during coding. Record divergences in `docs/decisions/`.
- **Session close:** run the session-close checklist in `docs/documentation-standard.md`.
  - Update phase status in `docs/product-roadmap.md`.
  - Keep `docs/reference/folder-structure.md` in sync with structural changes.
- Mark a roadmap item `shipped` only when its acceptance criteria pass.

## Operational Notes

- `backend/data/upu/*.json` are committed UPU snapshots.
  - Don't hand-edit them. Re-run the importer instead.
  - Be polite to KPT's server: run the importer sequentially, never in parallel bursts.
- Don't touch `sambungbelajarai/`, `archieve-sambung/`, or any `.venv/`.
