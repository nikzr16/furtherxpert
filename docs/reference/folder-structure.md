# Folder Structure Reference

> **Quick summary**
> - **What:** a map of where every part of FurtherXpert lives.
> - **Why:** so anyone can find the right file fast, and put new files in the right place.
> - **Now:** Phase 1 (foundation), Phase 2 (accounts, backend only), and Phase 3 (reference data) are built. Items marked *(planned)* come in later phases.

> **Type:** Reference | **Must stay current:** Yes -- update when structure, routes, schemas, or config change

<!-- AI Context
Role: This document records structural facts about the codebase: files,
modules, routes, schemas, config, and their relationships.
Treat it as a lookup table. When creating or modifying files, routes, or
schemas, update this document before the coding session ends.
If this document conflicts with a PRD or plan, this document reflects the
current state; record the divergence in the decision log.
-->

## Overview

The project has 3 running parts, started together by Docker Compose (a tool that runs several programs as one setup):

- **`backend/`**: the server (**API**). Python + FastAPI.
- **`client/`**: the website students see. React + Tailwind CSS + Recharts.
- **`db`**: the **database** (PostgreSQL). It has no folder, and its data lives in a Docker storage volume.

## Directory Layout

```text
furtherxpert/
├── CLAUDE.md, CLAUDE.project.md    harness policy, project brief
├── .claude/                        harness: agents, skills, workflows (proj-* = project)
├── docs/
│   ├── prd/furtherxpert-prd.md   the PRD: what and why (source of truth)
│   ├── plan/furtherxpert-plan.md the plan: how each phase is built
│   ├── furtherxpert-workflow.md     how the app behaves today
│   ├── product-roadmap.md          build order + status
│   ├── project-knowledge.md        background knowledge (starter)
│   ├── documentation-standard.md   how docs are kept
│   ├── layman-guide.md             how to write in plain words
│   ├── reference/                  this file
│   ├── decisions/                  decision log
│   └── templates/                  doc templates
├── docker-compose.yml              runs db + backend + client
├── .env.example                    settings template (copy to .env)
├── backend/
│   ├── pyproject.toml, uv.lock     Python packages (managed by uv)
│   ├── Dockerfile, .dockerignore
│   ├── alembic.ini                 migration tool settings
│   ├── migrations/                 database migrations
│   │   └── versions/
│   │       ├── fe17fc1fca80_add_users_table.py             creates the `users` table
│   │       ├── 57ab2a90bfa6_add_reference_data_tables.py   creates the reference-data tables (Phase 3)
│   │       └── 6676e66b52e5_load_2026_2027_upu_snapshot.py loads the sesi 2026/2027 snapshot (Phase 3)
│   ├── data/upu/                   e-Panduan snapshots
│   │   ├── 2026-2027.json          committed snapshot (Phase 3)
│   │   └── .cache/                 raw HTML resume cache -- gitignored, never committed
│   ├── app/
│   │   ├── main.py                 creates the app, CORS, routers
│   │   ├── api/health.py           GET /health
│   │   ├── api/deps.py             shared dependency: finds the logged-in user from the access token
│   │   ├── api/auth.py             POST /auth/register, /auth/login, /auth/refresh, /auth/logout
│   │   ├── api/me.py               GET /me, DELETE /me
│   │   ├── api/reference.py        GET /subjects, /universities, /programs, /programs/{code} (Phase 3)
│   │   ├── core/config.py          reads settings from .env
│   │   ├── core/db.py              database connection + Base
│   │   ├── core/security.py        makes/checks login tokens, scrambles passwords
│   │   ├── core/limiter.py         limits login/sign-up attempts (5 per minute per visitor)
│   │   ├── models/user.py          `users` table
│   │   ├── models/session.py       `sessions` table (Phase 3)
│   │   ├── models/university.py    `universities` table (Phase 3)
│   │   ├── models/subject.py       `subjects` + `subject_groups` tables (Phase 3)
│   │   ├── models/interest_area.py `interest_areas` table (Phase 3)
│   │   ├── models/program.py       `programs` + `campuses` tables (Phase 3)
│   │   ├── models/requirement.py   `general_requirements` + `program_requirements` tables (Phase 3)
│   │   ├── schemas/user.py         request/response shapes for accounts
│   │   ├── schemas/reference.py    request/response shapes for reference data (Phase 3)
│   │   ├── services/auth.py        sign-up and login rules (empty for scoring, eligibility, AI -- later phases)
│   │   ├── services/reference.py   reads subjects, universities, and programs for the routes (Phase 3)
│   │   └── importer/               e-Panduan importer (Phase 3)
│   │       ├── epanduan.py         fetches e-Panduan and writes the session snapshot
│   │       ├── subjects.py         hand-written Malay subject name -> subject code map
│   │       └── reference_data.py   university codes + PRD T1 interest-area mapping
│   └── tests/
│       ├── conftest.py             test setup (dummy settings + a real, separate test database for account tests)
│       ├── test_health.py          /health tests
│       ├── test_auth.py            account tests: sign up, log in, refresh, log out, view/delete account
│       ├── test_importer_epanduan.py   importer parser tests, on saved real e-Panduan pages (Phase 3)
│       ├── test_reference_routes.py    /subjects, /universities, /programs, /programs/{code} route tests (Phase 3)
│       ├── fixtures/               saved real e-Panduan HTML pages used by the importer tests (Phase 3)
│       └── golden/                 sample-student tests (planned, Phase 5)
├── client/
│   ├── package.json, package-lock.json
│   ├── Dockerfile, .dockerignore
│   ├── vite.config.js              Vite + Tailwind plugin
│   ├── index.html
│   └── src/
│       ├── main.jsx                starts React
│       ├── App.jsx                 app shell + routes
│       ├── api.js                  calls the backend (uses VITE_API_URL)
│       ├── index.css               Tailwind import
│       └── pages/Home.jsx          placeholder page, shows /health
├── sambungbelajarai/               old SambungBelajarmu code: read-only, never edit
└── archieve-sambung/               old SambungBelajarmu archive: read-only, never edit
```

## Backend

| File | Purpose |
|---|---|
| `backend/app/main.py` | Creates the FastAPI app. Allows only `FRONTEND_ORIGIN` (CORS). Plugs in routers |
| `backend/app/api/health.py` | `GET /health`: always HTTP 200, with `{"status":"ok","db":"ok"}` or `"db":"error"` |
| `backend/app/api/auth.py` | Account routes that don't need a login: register, log in, refresh, log out |
| `backend/app/api/me.py` | Account routes that need a login: view or delete the current account |
| `backend/app/api/deps.py` | Shared dependency (`get_current_user`): reads the `Authorization` header, checks the access token, and looks up the matching row in `users`. Every `/me` route uses this -- never a user id typed in the request itself |
| `backend/app/api/reference.py` | Reference-data routes, no login needed: `GET /subjects`, `GET /universities`, `GET /programs` (filter by `area`, `university`, `q`), `GET /programs/{code}` |
| `backend/app/core/config.py` | Loads the `.env` settings (pydantic-settings) |
| `backend/app/core/db.py` | SQLAlchemy engine, session, and `Base` for tables |
| `backend/app/core/security.py` | Creates and checks **JWT** (JSON Web Token, a signed login pass) access/refresh tokens; scrambles and checks passwords with **argon2** (a one-way password-scrambling method) |
| `backend/app/core/limiter.py` | Shared rate limiter (slowapi): caps login and sign-up at 5 tries per minute per visitor |
| `backend/app/models/user.py` | The `users` table definition (SQLAlchemy model) |
| `backend/app/models/session.py` | The `sessions` table: one row per yearly UPU intake session (e.g. "2026/2027") |
| `backend/app/models/university.py` | The `universities` table: public-university codes and names. Not session-scoped -- codes are stable across years |
| `backend/app/models/subject.py` | The `subject_groups` and `subjects` tables, seeded from `app/importer/subjects.py` |
| `backend/app/models/interest_area.py` | The `interest_areas` table: NEC code prefixes -> area name, and which subject groups count toward that area's "excel" score (PRD T1) |
| `backend/app/models/program.py` | The `programs` and `campuses` tables, loaded from a session snapshot -- never hand-edited |
| `backend/app/models/requirement.py` | The `general_requirements` (syarat am) and `program_requirements` (syarat khas) tables: the rule tree (`rules`), the original Malay text (`text_ms`), and an `unparsed` flag, per session/program and per UPU category (A/B) |
| `backend/app/schemas/user.py` | Pydantic request/response shapes for register, login, and the current-account view |
| `backend/app/schemas/reference.py` | Pydantic request/response shapes for the reference-data routes |
| `backend/app/services/auth.py` | Sign-up and login business rules: creates the account, checks the password, keeps login timing the same whether the email exists or not |
| `backend/app/services/reference.py` | Reference-data reads: subjects, universities, and programs (with `area`/`university`/`q` filters), always from the most recently loaded session |
| `backend/app/importer/epanduan.py` | Sequentially fetches e-Panduan's program lists and rule pages (1 request at a time, paused, retried with backoff), parses them with **selectolax** (decision `0002`), and writes a session snapshot |
| `backend/app/importer/subjects.py` | Hand-written list mapping every Malay subject name (and old-syllabus name) seen on e-Panduan to one subject code. Raises `UnknownSubjectError` on an unmapped name, which stops the import |
| `backend/app/importer/reference_data.py` | Hand-written university code -> name list (20 universities), and the PRD T1 interest-area mapping |
| `backend/migrations/env.py` | Alembic setup, linked to `Base.metadata` and `DATABASE_URL` |
| `backend/migrations/versions/fe17fc1fca80_add_users_table.py` | First real migration: creates the `users` table (see **Database tables** below) |
| `backend/migrations/versions/57ab2a90bfa6_add_reference_data_tables.py` | Second migration: creates the 9 reference-data tables. No rows loaded yet |
| `backend/migrations/versions/6676e66b52e5_load_2026_2027_upu_snapshot.py` | Third migration: seeds the shared tables (universities, subjects, subject_groups, interest_areas) and loads `backend/data/upu/2026-2027.json` into the session-scoped tables. Re-running it replaces that session's rows only |

## Routes

| Method | Path | Needs login? | Purpose |
|---|---|---|---|
| `GET` | `/health` | No | Server + database status check |
| `POST` | `/auth/register` | No | Create an account. Rejects a duplicate email, an unknown race value, or a missing consent tick |
| `POST` | `/auth/login` | No | Exchange email + password for a 15-minute access token, plus a refresh-token cookie |
| `POST` | `/auth/refresh` | No (cookie) | Exchange the refresh-token cookie for a new access token |
| `POST` | `/auth/logout` | No | Clears the refresh-token cookie |
| `GET` | `/me` | Yes | View the logged-in student's own account |
| `DELETE` | `/me` | Yes | Delete the logged-in student's own account (PDPA "delete my account") |
| `GET` | `/subjects` | No | List every SPM subject: code, Malay name, English name, subject group, old-syllabus flag |
| `GET` | `/universities` | No | List every public university's code and name |
| `GET` | `/programs` | No | List programs for the most recently loaded session. Optional filters: `area`, `university`, `q` (text search) |
| `GET` | `/programs/{code}` | No | One program's full detail: rules for both categories, original Malay text, source credit. `404` if the code isn't in the current session |

> **Watch out:** every `/me` route only ever acts on the account tied to the access token. A student can never read or delete another student's account, even if they guess an id.

## Database tables

| Table | Columns | Notes |
|---|---|---|
| `users` | `id` (UUID, primary key), `email` (unique, lower-cased), `password_hash`, `is_citizen` (bool), `race` (must be one of 7 fixed values, checked by the database), `spm_year` (int, range-checked by the database), `consent_at` (when sign-up consent was given), `created_at` | Added by migration `fe17fc1fca80`. `id` has no other meaning on purpose, so Phase 4's student tables (`spm_results`, `interest_answers`, `analysis`) can each point back at it with `ON DELETE CASCADE` -- deleting a user then removes every row that depends on it automatically |
| `sessions` | `id`, `name` (unique, e.g. "2026/2027"), `latest_spm_year`, `created_at` | Added by migration `57ab2a90bfa6`, loaded by `6676e66b52e5`. One row per yearly import. `latest_spm_year` decides which SPM year counts as category A (PRD T2) |
| `universities` | `id`, `code` (4 chars, unique, e.g. "UE"), `name` | Not session-scoped -- stable across years. 20 rows loaded, from the hand-written list in `app/importer/reference_data.py` |
| `subject_groups` | `id`, `code` (unique, e.g. "SCIENCES"), `name` | Seeded from `app/importer/subjects.py`, not scraped |
| `subjects` | `id`, `code` (unique), `name_ms`, `name_en`, `group_id`, `old_syllabus` (bool) | Seeded from `app/importer/subjects.py`. 117 rows loaded for sesi 2026/2027 |
| `interest_areas` | `id`, `name` (unique), `nec_prefixes` (JSON list), `exclude_nec_prefixes` (JSON list), `subject_groups` (JSON list) | Seeded from `app/importer/reference_data.py`, PRD T1's area table verbatim. 9 rows loaded |
| `programs` | `id`, `session_id`, `code` (e.g. "UE4481001", matches `^U[A-Z]4`), `university_id`, `name`, `nec_code`, `nec_name`, `level`, `mode`, `duration_value`, `duration_unit`, `avg_merit`, `stem`/`tvet`/`bumiputera_only`/`interview` (bool), `career_paths` (JSON list) | Loaded by migration `6676e66b52e5` from the session snapshot, never hand-edited. 166 category-A programs loaded for sesi 2026/2027, across 11 of the 20 universities |
| `campuses` | `id`, `program_id`, `name` | One row per campus a program is offered at |
| `general_requirements` | `id`, `session_id`, `category` ("A" or "B"), `rules` (JSON rule tree), `text_ms` (original Malay text), `unparsed` (bool) | Syarat am: same for every program in a session + category |
| `program_requirements` | `id`, `program_id`, `category` ("A" or "B"), `rules` (JSON rule tree), `text_ms`, `unparsed` (bool) | Syarat khas: one row per program per category. 328 rows loaded for sesi 2026/2027 -- 100% fully parsed (no `unparsed` rows); `unverifiable` entries are interview notes only |

## Client

| File | Purpose |
|---|---|
| `client/src/App.jsx` | Header "FurtherXpert" + page routes |
| `client/src/api.js` | Small helper for backend calls |
| `client/src/pages/Home.jsx` | Placeholder home page that shows the server status |

## Docker services

| Service | Port | What it does |
|---|---|---|
| `db` | 5432 | PostgreSQL 16, with a health check |
| `backend` | 8000 | Runs `uv run alembic upgrade head`, then the server with auto-reload |
| `client` | 5173 | Vite dev server |

## Wiring

- **Start order:** `db` becomes healthy → `backend` runs migrations, then starts → `client` starts.
- **Routers:** each file in `backend/app/api/` exposes a `router`. `main.py` plugs it in with `app.include_router(...)`.
- **Settings:** every service reads the repo-root `.env`. The client reads `VITE_API_URL` to find the backend.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals behind these structures (T2, T5, T6, T8) |
| `docs/product-roadmap.md` | Roadmap | Which phase adds each *(planned)* item |
| `docs/decisions/NNNN-*.md` | Decision log | Structural changes that diverged from the plan |
