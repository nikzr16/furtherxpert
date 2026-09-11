# Folder Structure Reference

> **Quick summary**
> - **What:** a map of where every part of SambungBelajarmu.ai v2 lives.
> - **Why:** so anyone can find the right file fast, and put new files in the right place.
> - **Now:** Phase 1 (foundation) is built. Items marked *(planned)* come in later phases.

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
│   ├── decisions/                  decision log (empty so far)
│   └── templates/                  doc templates
├── docker-compose.yml              runs db + backend + client
├── .env.example                    settings template (copy to .env)
├── backend/
│   ├── pyproject.toml, uv.lock     Python packages (managed by uv)
│   ├── Dockerfile, .dockerignore
│   ├── alembic.ini                 migration tool settings
│   ├── migrations/                 database migrations (no tables yet)
│   ├── data/upu/                   e-Panduan snapshots (planned, Phase 3)
│   ├── app/
│   │   ├── main.py                 creates the app, CORS, routers
│   │   ├── api/health.py           GET /health
│   │   ├── core/config.py          reads settings from .env
│   │   ├── core/db.py              database connection + Base
│   │   ├── models/                 database tables (empty)
│   │   ├── schemas/                request/response shapes (empty)
│   │   ├── services/               scoring, eligibility, auth, AI (empty)
│   │   └── importer/               e-Panduan importer (planned, Phase 3)
│   └── tests/
│       ├── conftest.py             test setup (dummy settings)
│       ├── test_health.py          /health tests
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
| `backend/app/core/config.py` | Loads the `.env` settings (pydantic-settings) |
| `backend/app/core/db.py` | SQLAlchemy engine, session, and `Base` for tables |
| `backend/migrations/env.py` | Alembic setup, linked to `Base.metadata` and `DATABASE_URL` |

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
