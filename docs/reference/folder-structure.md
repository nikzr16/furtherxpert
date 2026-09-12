# Folder Structure Reference

> **Quick summary**
> - **What:** a map of where every part of FurtherXpert lives.
> - **Why:** so anyone can find the right file fast, and put new files in the right place.
> - **Now:** Phase 1 (foundation), Phase 2 (accounts, backend only), Phase 3 (reference data), Phase 4 (student input, backend only), and Phase 5 (rules engine, backend only) are built. Items marked *(planned)* come in later phases.

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
│   │       ├── 6676e66b52e5_load_2026_2027_upu_snapshot.py loads the sesi 2026/2027 snapshot (Phase 3)
│   │       ├── 23947a34f766_add_student_input_tables.py    creates the student-input tables (Phase 4)
│   │       ├── 1fa628967fac_seed_approved_interest_test.py loads the approved interest test (Phase 4)
│   │       └── 3916bef04fb3_add_analysis_table.py          creates the `analysis` cache table (Phase 5)
│   ├── data/
│   │   ├── interest_test.json      the 20 approved interest-test questions (Phase 4)
│   │   └── upu/                    e-Panduan snapshots
│   │       ├── 2026-2027.json      committed snapshot (Phase 3)
│   │       └── .cache/             raw HTML resume cache -- gitignored, never committed
│   ├── app/
│   │   ├── main.py                 creates the app, CORS, routers
│   │   ├── api/health.py           GET /health
│   │   ├── api/deps.py             shared dependency: finds the logged-in user from the access token
│   │   ├── api/auth.py             POST /auth/register, /auth/login, /auth/refresh, /auth/logout
│   │   ├── api/me.py               GET /me, DELETE /me, GET+PUT /me/results, PUT /me/interest-answers (Phase 4), GET /me/analysis (Phase 5)
│   │   ├── api/reference.py        GET /subjects, /universities, /programs, /programs/{code} (Phase 3)
│   │   ├── api/interest_test.py    GET /interest-test (Phase 4)
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
│   │   ├── models/spm_result.py    `spm_results` table (Phase 4)
│   │   ├── models/interest_test.py `interest_questions` + `interest_options` + `interest_answers` tables (Phase 4)
│   │   ├── models/analysis.py      `analysis` cache table (Phase 5)
│   │   ├── schemas/user.py         request/response shapes for accounts
│   │   ├── schemas/reference.py    request/response shapes for reference data (Phase 3)
│   │   ├── schemas/spm_result.py   request/response shapes for SPM results (Phase 4)
│   │   ├── schemas/interest_test.py request/response shapes for the interest test (Phase 4)
│   │   ├── schemas/analysis.py     response shape for GET /me/analysis (Phase 5)
│   │   ├── services/auth.py        sign-up and login rules (empty for AI -- later phase)
│   │   ├── services/reference.py   reads subjects, universities, and programs for the routes (Phase 3)
│   │   ├── services/results.py     reads and upserts a student's SPM results, invalidates the analysis cache (Phase 4, Phase 5)
│   │   ├── services/interest_test.py reads the question list and replaces a student's answers, invalidates the analysis cache (Phase 4, Phase 5)
│   │   ├── services/scoring.py     Chart scoring, Best Fit sort/filter -- pure functions, no DB (Phase 5)
│   │   ├── services/eligibility.py UPU eligibility checker -- pure functions, no DB (Phase 5)
│   │   ├── services/analysis.py    GET /me/analysis orchestration: loads DB data, calls scoring.py/eligibility.py, caches the result (Phase 5)
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
│       ├── test_student_input.py   /me/results and interest-test route tests, incl. delete-account cascade (Phase 4)
│       ├── test_scoring.py         unit tests for services/scoring.py -- pure functions, no DB (Phase 5)
│       ├── test_eligibility.py     unit tests for services/eligibility.py, incl. the counts-once trap (Phase 5)
│       ├── test_analysis.py        API tests for GET /me/analysis: caching, invalidation, cross-user isolation, category A/B, non-citizen (Phase 5)
│       ├── fixtures/               saved real e-Panduan HTML pages used by the importer tests (Phase 3)
│       └── golden/                 6 sample-student golden tests, run against the real API + DB (Phase 5)
│           ├── students.json           each student's SPM results and interest-test picks (hand-derived)
│           ├── expected/*.json         each student's expected chart/Best Fit numbers, with a derivation note
│           └── test_golden_students.py the test file: drives the real API, plus 3 eligibility spot-checks
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
| `backend/app/api/me.py` | Account routes that need a login: view or delete the current account, save/read SPM results, save interest-test answers (Phase 4), read the computed charts/Best Fit/eligibility (`GET /me/analysis`, Phase 5) |
| `backend/app/api/deps.py` | Shared dependency (`get_current_user`): reads the `Authorization` header, checks the access token, and looks up the matching row in `users`. Every `/me` route uses this -- never a user id typed in the request itself |
| `backend/app/api/reference.py` | Reference-data routes, no login needed: `GET /subjects`, `GET /universities`, `GET /programs` (filter by `area`, `university`, `q`), `GET /programs/{code}` |
| `backend/app/api/interest_test.py` | `GET /interest-test`: the 20 questions and their options, no login needed. Never returns which option maps to which interest area (Phase 4) |
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
| `backend/app/models/spm_result.py` | The `spm_results` table: one row per subject a student has entered a grade for. `ON DELETE CASCADE` to `users`. Defines `SPM_GRADES`, the 10 allowed grades |
| `backend/app/models/interest_test.py` | The `interest_questions`, `interest_options` (each tagged to an interest area, or untagged for "None of the above"), and `interest_answers` (`ON DELETE CASCADE` to `users`) tables |
| `backend/app/models/analysis.py` | The `analysis` table: one cached row per user (`user_id` is the primary key, not a surrogate `id`), `ON DELETE CASCADE` to `users`. Holds the full `GET /me/analysis` response as JSONB plus its own `computed_at` (Phase 5) |
| `backend/app/schemas/user.py` | Pydantic request/response shapes for register, login, and the current-account view |
| `backend/app/schemas/reference.py` | Pydantic request/response shapes for the reference-data routes |
| `backend/app/schemas/spm_result.py` | Pydantic request/response shapes for `GET`/`PUT /me/results`. Validates the grade is one of `SPM_GRADES` |
| `backend/app/schemas/interest_test.py` | Pydantic request/response shapes for `GET /interest-test` and `PUT /me/interest-answers`. The public option shape carries no area id or name |
| `backend/app/schemas/analysis.py` | Pydantic response shape for `GET /me/analysis`: both charts, Best Fit, Sweet spot, category, `computed_at` (Phase 5) |
| `backend/app/services/auth.py` | Sign-up and login business rules: creates the account, checks the password, keeps login timing the same whether the email exists or not |
| `backend/app/services/reference.py` | Reference-data reads: subjects, universities, and programs (with `area`/`university`/`q` filters), always from the most recently loaded session |
| `backend/app/services/results.py` | SPM-results read and upsert: validates subject codes against the database, requires Bahasa Melayu (`BM`) and Sejarah (`SJ`) in every save, never deletes a subject the payload leaves out. Also deletes the student's cached `analysis` row on every successful save (Phase 5) |
| `backend/app/services/interest_test.py` | Interest-test reads (question list with options) and answer replacement: a retake deletes all of a student's previous answers and inserts the new set in one transaction. Also deletes the student's cached `analysis` row on every successful save (Phase 5) |
| `backend/app/services/scoring.py` | **Pure functions, no DB session, no HTTP, no clock:** grade-to-percent, subject-group scores (Chart 1), interest-area scores (Chart 2), excel scores, top-3-with-tiebreak, Sweet spot, and Best Fit's program sort/filter (Phase 5) |
| `backend/app/services/eligibility.py` | **Pure functions, no DB session, no HTTP, no clock:** the UPU eligibility checker. Merges syarat am + syarat khas into one rule tree and checks it with backtracking so each subject counts at most once across the whole tree (decision `0005`); returns a verdict (Eligible/Conditional/Not Eligible) with plain-English reasons (Phase 5) |
| `backend/app/services/analysis.py` | `GET /me/analysis` orchestration: the one Phase 5 module that touches the DB and the clock. Loads a student's grades/answers/category and the current session's reference data, calls `scoring.py`/`eligibility.py`, builds Best Fit, caches the result in `analysis`. Raises `MissingGeneralRequirementsError` if the session has no syarat am row for the student's category (Phase 5) |
| `backend/app/importer/epanduan.py` | Sequentially fetches e-Panduan's program lists and rule pages (1 request at a time, paused, retried with backoff), parses them with **selectolax** (decision `0002`), and writes a session snapshot |
| `backend/app/importer/subjects.py` | Hand-written list mapping every Malay subject name (and old-syllabus name) seen on e-Panduan to one subject code. Raises `UnknownSubjectError` on an unmapped name, which stops the import |
| `backend/app/importer/reference_data.py` | Hand-written university code -> name list (20 universities), and the PRD T1 interest-area mapping |
| `backend/migrations/env.py` | Alembic setup, linked to `Base.metadata` and `DATABASE_URL` |
| `backend/migrations/versions/fe17fc1fca80_add_users_table.py` | First real migration: creates the `users` table (see **Database tables** below) |
| `backend/migrations/versions/57ab2a90bfa6_add_reference_data_tables.py` | Second migration: creates the 9 reference-data tables. No rows loaded yet |
| `backend/migrations/versions/6676e66b52e5_load_2026_2027_upu_snapshot.py` | Third migration: seeds the shared tables (universities, subjects, subject_groups, interest_areas) and loads `backend/data/upu/2026-2027.json` into the session-scoped tables. Re-running it replaces that session's rows only |
| `backend/migrations/versions/23947a34f766_add_student_input_tables.py` | Fourth migration: creates `spm_results`, `interest_questions`, `interest_options`, and `interest_answers`. No rows loaded yet |
| `backend/migrations/versions/1fa628967fac_seed_approved_interest_test.py` | Fifth migration: loads `backend/data/interest_test.json` (the 20 product owner-approved questions) into `interest_questions`/`interest_options`, tagging each option to its interest area. Re-running it fully replaces every question and option -- see decision `0004` for why it doesn't key the replace on the file's `version` field |
| `backend/migrations/versions/3916bef04fb3_add_analysis_table.py` | Sixth migration: creates the `analysis` table (see **Database tables** below). No rows loaded -- it's filled the first time each student calls `GET /me/analysis` |

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
| `GET` | `/interest-test` | No | List all 20 interest-test questions and their options. Never reveals which option maps to which interest area |
| `GET` | `/me/results` | Yes | The logged-in student's own saved SPM results |
| `PUT` | `/me/results` | Yes | Upsert (update-or-insert) SPM results. Requires `BM` and `SJ` in the payload, rejects bad grades, duplicate subjects, or unknown subject codes |
| `PUT` | `/me/interest-answers` | Yes | Replace the logged-in student's interest-test answers. A retake fully replaces the old set. Rejects duplicate question ids, unknown question/option ids, or an option that doesn't belong to its question |
| `GET` | `/me/analysis` | Yes | The logged-in student's both charts, Likely to excel/love, Sweet spot, Best Fit (up to 3 programs per area, Eligible/Conditional only), and category (A/B). Cached until the student's results or answers change |

> **Watch out:** every `/me` route only ever acts on the account tied to the access token. A student can never read or delete another student's account, results, or interest answers, even if they guess an id.

## Database tables

| Table | Columns | Notes |
|---|---|---|
| `users` | `id` (UUID, primary key), `email` (unique, lower-cased), `password_hash`, `is_citizen` (bool), `race` (must be one of 7 fixed values, checked by the database), `spm_year` (int, range-checked by the database), `consent_at` (when sign-up consent was given), `created_at` | Added by migration `fe17fc1fca80`. `id` has no other meaning on purpose, so student tables (`spm_results`, `interest_answers`, and Phase 5's `analysis`) can each point back at it with `ON DELETE CASCADE` -- deleting a user then removes every row that depends on it automatically |
| `sessions` | `id`, `name` (unique, e.g. "2026/2027"), `latest_spm_year`, `created_at` | Added by migration `57ab2a90bfa6`, loaded by `6676e66b52e5`. One row per yearly import. `latest_spm_year` decides which SPM year counts as category A (PRD T2) |
| `universities` | `id`, `code` (4 chars, unique, e.g. "UE"), `name` | Not session-scoped -- stable across years. 20 rows loaded, from the hand-written list in `app/importer/reference_data.py` |
| `subject_groups` | `id`, `code` (unique, e.g. "SCIENCES"), `name` | Seeded from `app/importer/subjects.py`, not scraped |
| `subjects` | `id`, `code` (unique), `name_ms`, `name_en`, `group_id`, `old_syllabus` (bool) | Seeded from `app/importer/subjects.py`. 117 rows loaded for sesi 2026/2027 |
| `interest_areas` | `id`, `name` (unique), `nec_prefixes` (JSON list), `exclude_nec_prefixes` (JSON list), `subject_groups` (JSON list) | Seeded from `app/importer/reference_data.py`, PRD T1's area table verbatim. 9 rows loaded |
| `programs` | `id`, `session_id`, `code` (e.g. "UE4481001", matches `^U[A-Z]4`), `university_id`, `name`, `nec_code`, `nec_name`, `level`, `mode`, `duration_value`, `duration_unit`, `avg_merit`, `stem`/`tvet`/`bumiputera_only`/`interview` (bool), `career_paths` (JSON list) | Loaded by migration `6676e66b52e5` from the session snapshot, never hand-edited. 166 category-A programs loaded for sesi 2026/2027, across 11 of the 20 universities |
| `campuses` | `id`, `program_id`, `name` | One row per campus a program is offered at |
| `general_requirements` | `id`, `session_id`, `category` ("A" or "B"), `rules` (JSON rule tree), `text_ms` (original Malay text), `unparsed` (bool) | Syarat am: same for every program in a session + category |
| `program_requirements` | `id`, `program_id`, `category` ("A" or "B"), `rules` (JSON rule tree), `text_ms`, `unparsed` (bool) | Syarat khas: one row per program per category. 328 rows loaded for sesi 2026/2027 -- 100% fully parsed (no `unparsed` rows); `unverifiable` entries are interview notes only |
| `spm_results` | `id`, `user_id` (FK `users`, `ON DELETE CASCADE`), `subject_id` (FK `subjects`), `grade` (checked by the database against the 10 allowed grades) | Added by migration `23947a34f766` (Phase 4). One row per subject a student has saved a grade for. Unique per (`user_id`, `subject_id`) -- `PUT /me/results` upserts on that pair |
| `interest_questions` | `id`, `n` (unique, 1-20, the question's number in the approved set), `text` | Added by migration `23947a34f766`, loaded by `1fa628967fac` (Phase 4). The 20 product owner-approved questions from `backend/data/interest_test.json` |
| `interest_options` | `id`, `question_id` (FK `interest_questions`, `ON DELETE CASCADE`), `text`, `area_id` (FK `interest_areas`, nullable) | Added by migration `23947a34f766`, loaded by `1fa628967fac`. 4 area-tagged options per question, plus one "None of the above" option with `area_id` NULL |
| `interest_answers` | `id`, `user_id` (FK `users`, `ON DELETE CASCADE`), `question_id` (FK `interest_questions`), `chosen_option_id` (FK `interest_options`) | Added by migration `23947a34f766` (Phase 4). One row per (`user_id`, `question_id`) the student has answered -- unique on that pair. `PUT /me/interest-answers` deletes and reinserts all of a student's rows on every save (a retake), so a partial answer set is allowed |
| `analysis` | `user_id` (FK `users`, `ON DELETE CASCADE`, **primary key** -- one row per user, not a surrogate `id`), `result` (JSONB, the full `GET /me/analysis` response), `computed_at` (its own real `DateTime`, redundant with `result["computed_at"]` so a caller can order/filter without parsing JSON) | Added by migration `3916bef04fb3` (Phase 5). A cache: the first `GET /me/analysis` after a change computes and saves a row here; later `GET`s are served from it unchanged. `PUT /me/results` and `PUT /me/interest-answers` delete the student's row here on every successful save (decision `0006`), so it never goes stale |

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
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals behind these structures (T1, T2, T5, T6, T8) |
| `docs/product-roadmap.md` | Roadmap | Which phase adds each *(planned)* item |
| `docs/decisions/NNNN-*.md` | Decision log | Structural changes that diverged from the plan |
