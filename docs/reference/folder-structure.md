# Folder Structure Reference

> **Quick summary**
> - **What:** a map of where every part of SambungBelajarmu.ai v2 lives.
> - **Why:** so anyone can find the right file fast, and put new files in the right place.
> - **Now:** Phase 1 (foundation) and Phase 2 (accounts, backend only) are built. Items marked *(planned)* come in later phases.

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
│   ├── prd/sambungbelajarmu-v2-prd.md   the PRD (source of truth)
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
│   │   └── versions/fe17fc1fca80_add_users_table.py   creates the `users` table
│   ├── data/upu/                   e-Panduan snapshots (planned, Phase 3)
│   ├── app/
│   │   ├── main.py                 creates the app, CORS, routers
│   │   ├── api/health.py           GET /health
│   │   ├── api/deps.py             shared dependency: finds the logged-in user from the access token
│   │   ├── api/auth.py             POST /auth/register, /auth/login, /auth/refresh, /auth/logout
│   │   ├── api/me.py               GET /me, DELETE /me
│   │   ├── core/config.py          reads settings from .env
│   │   ├── core/db.py              database connection + Base
│   │   ├── core/security.py        makes/checks login tokens, scrambles passwords
│   │   ├── core/limiter.py         limits login/sign-up attempts (5 per minute per visitor)
│   │   ├── models/user.py          `users` table
│   │   ├── schemas/user.py         request/response shapes for accounts
│   │   ├── services/auth.py        sign-up and login rules (empty for scoring, eligibility, AI -- later phases)
│   │   └── importer/               e-Panduan importer (planned, Phase 3)
│   └── tests/
│       ├── conftest.py             test setup (dummy settings + a real, separate test database for account tests)
│       ├── test_health.py          /health tests
│       ├── test_auth.py            account tests: sign up, log in, refresh, log out, view/delete account
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
├── sambungbelajarai/               v1 code: read-only, never edit
└── archieve-sambung/               v1 archive: read-only, never edit
```

## Backend

| File | Purpose |
|---|---|
| `backend/app/main.py` | Creates the FastAPI app. Allows only `FRONTEND_ORIGIN` (CORS). Plugs in routers |
| `backend/app/api/health.py` | `GET /health`: always HTTP 200, with `{"status":"ok","db":"ok"}` or `"db":"error"` |
| `backend/app/api/auth.py` | Account routes that don't need a login: register, log in, refresh, log out |
| `backend/app/api/me.py` | Account routes that need a login: view or delete the current account |
| `backend/app/api/deps.py` | Shared dependency (`get_current_user`): reads the `Authorization` header, checks the access token, and looks up the matching row in `users`. Every `/me` route uses this -- never a user id typed in the request itself |
| `backend/app/core/config.py` | Loads the `.env` settings (pydantic-settings) |
| `backend/app/core/db.py` | SQLAlchemy engine, session, and `Base` for tables |
| `backend/app/core/security.py` | Creates and checks **JWT** (JSON Web Token, a signed login pass) access/refresh tokens; scrambles and checks passwords with **argon2** (a one-way password-scrambling method) |
| `backend/app/core/limiter.py` | Shared rate limiter (slowapi): caps login and sign-up at 5 tries per minute per visitor |
| `backend/app/models/user.py` | The `users` table definition (SQLAlchemy model) |
| `backend/app/schemas/user.py` | Pydantic request/response shapes for register, login, and the current-account view |
| `backend/app/services/auth.py` | Sign-up and login business rules: creates the account, checks the password, keeps login timing the same whether the email exists or not |
| `backend/migrations/env.py` | Alembic setup, linked to `Base.metadata` and `DATABASE_URL` |
| `backend/migrations/versions/fe17fc1fca80_add_users_table.py` | First real migration: creates the `users` table (see **Database tables** below) |

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

> **Watch out:** every `/me` route only ever acts on the account tied to the access token. A student can never read or delete another student's account, even if they guess an id.

## Database tables

| Table | Columns | Notes |
|---|---|---|
| `users` | `id` (UUID, primary key), `email` (unique, lower-cased), `password_hash`, `is_citizen` (bool), `race` (must be one of 7 fixed values, checked by the database), `spm_year` (int, range-checked by the database), `consent_at` (when sign-up consent was given), `created_at` | Added by migration `fe17fc1fca80`. `id` has no other meaning on purpose, so Phase 4's student tables (`spm_results`, `interest_answers`, `analysis`) can each point back at it with `ON DELETE CASCADE` -- deleting a user then removes every row that depends on it automatically |

## Client

| File | Purpose |
|---|---|
| `client/src/App.jsx` | Header "SambungBelajarmu.ai" + page routes |
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
| `docs/prd/sambungbelajarmu-v2-prd.md` | Intent | Product goals behind these structures (T5, T6, T8) |
| `docs/product-roadmap.md` | Roadmap | Which phase adds each *(planned)* item |
| `docs/decisions/NNNN-*.md` | Decision log | Structural changes that diverged from the plan |
