# Folder Structure Reference

> **Quick summary**
> - **What:** a map of where every part of FurtherXpert lives.
> - **Why:** so anyone can find the right file fast, and put new files in the right place.
> - **Now:** all 7 phases are built -- foundation, accounts, reference data, student input, rules engine, client pages (all 8 screens), and Phase 7 (AI summary). This is the final phase of the first release; there are no *(planned)* items left. Phase 8 (UI redesign) added shared client pieces and a 404 page (client files only).

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
│   ├── prd/ui-redesign-prd.md    Phase 8 PRD: the UI redesign
│   ├── plan/furtherxpert-plan.md the plan: how each phase is built
│   ├── plan/ui-redesign-plan.md  Phase 8 plan + Definition of Done
│   ├── furtherxpert-workflow.md     how the app behaves today
│   ├── product-roadmap.md          build order + status
│   ├── project-knowledge.md        background knowledge (starter)
│   ├── documentation-standard.md   how docs are kept
│   ├── layman-guide.md             how to write in plain words
│   ├── reference/                  this file
│   ├── decisions/                  decision log
│   └── templates/                  doc templates
├── docker-compose.yml              runs db + backend + client (backend reload polls `app/` only; see Wiring)
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
│   │       ├── 3916bef04fb3_add_analysis_table.py          creates the `analysis` cache table (Phase 5)
│   │       └── 96f63a9f3e5c_add_ai_summary_columns_to_analysis.py adds `summary`/`summary_computed_at` to `analysis` (Phase 7)
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
│   │   ├── api/me.py               GET /me, DELETE /me, GET+PUT /me/results, GET+PUT /me/interest-answers (Phase 4, Phase 6), GET /me/analysis (Phase 5), GET /me/analysis/summary (Phase 7)
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
│   │   ├── models/analysis.py      `analysis` cache table (Phase 5; `summary`/`summary_computed_at` columns added Phase 7)
│   │   ├── schemas/user.py         request/response shapes for accounts
│   │   ├── schemas/reference.py    request/response shapes for reference data (Phase 3)
│   │   ├── schemas/spm_result.py   request/response shapes for SPM results (Phase 4)
│   │   ├── schemas/interest_test.py request/response shapes for the interest test (Phase 4)
│   │   ├── schemas/analysis.py     response shapes for GET /me/analysis (Phase 5) and GET /me/analysis/summary (Phase 7)
│   │   ├── services/auth.py        sign-up and login rules (empty for AI -- later phase)
│   │   ├── services/reference.py   reads subjects, universities, and programs for the routes (Phase 3)
│   │   ├── services/results.py     reads and upserts a student's SPM results, invalidates the analysis cache (Phase 4, Phase 5)
│   │   ├── services/interest_test.py reads the question list and replaces a student's answers, invalidates the analysis cache (Phase 4, Phase 5)
│   │   ├── services/scoring.py     Chart scoring, Best Fit sort/filter -- pure functions, no DB (Phase 5)
│   │   ├── services/eligibility.py UPU eligibility checker -- pure functions, no DB (Phase 5)
│   │   ├── services/analysis.py    GET /me/analysis orchestration: loads DB data, calls scoring.py/eligibility.py, caches the result (Phase 5); get_analysis_summary for GET /me/analysis/summary (Phase 7)
│   │   ├── services/ai_summary.py  builds the privacy-minimal GPT-5 prompt, calls OpenAI with a 6s timeout, enforces the 120-word cap in code (Phase 7)
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
│       ├── test_ai_summary.py      API tests for GET /me/analysis/summary: payload privacy, forced AI failure, timeout, caching/invalidation, cross-user isolation, not-enough-data, 120-word truncation -- all mock the OpenAI client (Phase 7)
│       ├── fixtures/               saved real e-Panduan HTML pages used by the importer tests (Phase 3)
│       └── golden/                 6 sample-student golden tests, run against the real API + DB (Phase 5)
│           ├── students.json           each student's SPM results and interest-test picks (hand-derived)
│           ├── expected/*.json         each student's expected chart/Best Fit numbers, with a derivation note
│           └── test_golden_students.py the test file: drives the real API, plus 3 eligibility spot-checks
├── client/
│   ├── package.json, package-lock.json
│   ├── Dockerfile, .dockerignore
│   ├── vite.config.js              Vite + Tailwind plugin; polls for file changes (`usePolling`) since Docker on Windows doesn't pass file-change events into the container, so hot-reload works
│   ├── index.html
│   └── src/
│       ├── main.jsx                starts React
│       ├── App.jsx                 app shell + routes (Phase 6)
│       ├── api.js                  calls the backend (uses VITE_API_URL) (Phase 6)
│       ├── constants.js            shared constants: SPM grade list, required subjects (Phase 6), all 7 subject groups (decision 0019)
│       ├── programName.js          cleans e-Panduan markers ("#", "Baru") out of program names and title-cases them for display (decisions 0009, 0016)
│       ├── index.css               Tailwind import, theme font, shared style classes (.btn, .card, .input...) (Phase 8)
│       ├── context/
│       │   └── AuthContext.jsx     holds the access token in memory, silent refresh on load, retry-once-on-401 (Phase 6)
│       ├── components/
│       │   ├── ui.jsx              shared pieces: icons, logo, page header, alerts, badges, loaders, error state (Phase 8)
│       │   ├── Nav.jsx             sticky top menu, folds into a menu button on phones (Phase 8)
│       │   ├── Footer.jsx          site footer with links and the e-Panduan data credit (Phase 8)
│       │   ├── AuthShell.jsx       two-panel layout for Log in and Register (Phase 8)
│       │   ├── ProtectedRoute.jsx  sends a logged-out visitor to Login instead of the page
│       │   ├── RadarChartCard.jsx  reusable radar chart with name + score spoke labels (decision 0017) + a real <table> text fallback (WCAG AA) + empty states
│       │   ├── EligibilityBadge.jsx eligibility verdict pill (VerdictPill) and reasons (ReasonList)
│       │   └── AISummaryCard.jsx   AI summary card; fetches GET /me/analysis/summary independently of the charts (Phase 7)
│       └── pages/
│           ├── Home.jsx            landing page: headline, example chart, live program counts, how it works (Phase 8)
│           ├── NotFound.jsx        "Page not found" page for unknown addresses (Phase 8)
│           ├── Register.jsx        sign-up form, explains the race question, collects consent (Phase 6)
│           ├── Login.jsx           log-in form, generic wrong-credentials message (Phase 6)
│           ├── SpmResults.jsx      SPM subject + grade rows, BM/Sejarah required (Phase 6)
│           ├── InterestTest.jsx    20 questions, save-as-you-go, resumes via GET /me/interest-answers (Phase 6)
│           ├── MyResults.jsx       AI summary card, both radar charts, Best Fit, eligibility badges (Phase 6; AI summary card added Phase 7)
│           ├── Explore.jsx         browse/filter all programs, client-side filtering (Phase 6)
│           ├── ProgramDetail.jsx   full program detail, Malay rule text, source credit (Phase 6)
│           └── Account.jsx         account info, log out, 2-step delete confirmation (Phase 6)
├── sambungbelajarai/               old SambungBelajarmu code: read-only, never edit
└── archieve-sambung/               old SambungBelajarmu archive: read-only, never edit
```

## Backend

| File | Purpose |
|---|---|
| `backend/app/main.py` | Creates the FastAPI app. Allows only `FRONTEND_ORIGIN` (CORS). Plugs in routers |
| `backend/app/api/health.py` | `GET /health`: always HTTP 200, with `{"status":"ok","db":"ok"}` or `"db":"error"` |
| `backend/app/api/auth.py` | Account routes that don't need a login: register, log in, refresh, log out |
| `backend/app/api/me.py` | Account routes that need a login: view or delete the current account, save/read SPM results, read/save interest-test answers (Phase 4; `GET /me/interest-answers` resume/progress added Phase 6), read the computed charts/Best Fit/eligibility (`GET /me/analysis`, Phase 5), read the AI summary (`GET /me/analysis/summary`, Phase 7) |
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
| `backend/app/models/analysis.py` | The `analysis` table: one cached row per user (`user_id` is the primary key, not a surrogate `id`), `ON DELETE CASCADE` to `users`. Holds the full `GET /me/analysis` response as JSONB plus its own `computed_at` (Phase 5), and (Phase 7) nullable `summary`/`summary_computed_at` columns for the cached AI summary text -- same row, so it inherits the charts' cache invalidation for free (decision `0011`) |
| `backend/app/schemas/user.py` | Pydantic request/response shapes for register, login, and the current-account view |
| `backend/app/schemas/reference.py` | Pydantic request/response shapes for the reference-data routes |
| `backend/app/schemas/spm_result.py` | Pydantic request/response shapes for `GET`/`PUT /me/results`. Validates the grade is one of `SPM_GRADES` |
| `backend/app/schemas/interest_test.py` | Pydantic request/response shapes for `GET /interest-test`, `GET`/`PUT /me/interest-answers`. The public option shape carries no area id or name. `InterestAnswersProgressOut` (Phase 6) is the saved-answers + `complete` shape for resuming a part-finished test |
| `backend/app/schemas/analysis.py` | Pydantic response shapes: `AnalysisOut` for `GET /me/analysis` -- both charts, Best Fit, Sweet spot, category, `computed_at`, `interest_test_complete` (Phase 5; `interest_test_complete` added Phase 6, decision `0008`); `AnalysisSummaryOut` for `GET /me/analysis/summary` -- `status` (`not_enough_data`/`ok`/`unavailable`), `summary`, `message` (Phase 7) |
| `backend/app/services/auth.py` | Sign-up and login business rules: creates the account, checks the password, keeps login timing the same whether the email exists or not |
| `backend/app/services/reference.py` | Reference-data reads: subjects, universities, and programs (with `area`/`university`/`q` filters), always from the most recently loaded session |
| `backend/app/services/results.py` | SPM-results read and upsert: validates subject codes against the database, requires Bahasa Melayu (`BM`) and Sejarah (`SJ`) in every save, never deletes a subject the payload leaves out. Also deletes the student's cached `analysis` row on every successful save (Phase 5) |
| `backend/app/services/interest_test.py` | Interest-test reads (question list with options) and `save_answers` (merge/upsert, decision `0008`, was a full replace before Phase 6): each save updates or inserts only the payload's questions, leaving every other saved answer untouched. Also deletes the student's cached `analysis` row on every successful save (Phase 5). `get_progress` (Phase 6) returns the student's saved answers plus whether all 20 are answered, for `GET /me/interest-answers` |
| `backend/app/services/scoring.py` | **Pure functions, no DB session, no HTTP, no clock:** grade-to-percent, subject-group scores (Chart 1), interest-area scores (Chart 2), excel scores, top-3-with-tiebreak, Sweet spot, and Best Fit's program sort/filter (Phase 5) |
| `backend/app/services/eligibility.py` | **Pure functions, no DB session, no HTTP, no clock:** the UPU eligibility checker. Merges syarat am + syarat khas into one rule tree and checks it with backtracking so each subject counts at most once across the whole tree (decision `0005`); returns a verdict (Eligible/Conditional/Not Eligible) with plain-English reasons (Phase 5) |
| `backend/app/services/ai_summary.py` | `generate_summary(area_scores, group_scores)`: the whole privacy boundary between the app and OpenAI (decision `0010`) -- only interest-area and subject-group names + scores are accepted as parameters, never email/race/citizenship/grades/user id. Calls the real `openai` SDK with a 6-second hard timeout and `max_retries=0` (decision `0012`), then deterministically truncates the reply to `MAX_SUMMARY_WORDS` (120) via `_enforce_word_limit` (decision `0013`). Raises `AISummaryError` on any failure -- never swallows one into an empty string (Phase 7) |
| `backend/app/services/analysis.py` | `GET /me/analysis` orchestration: the one Phase 5 module that touches the DB and the clock. Loads a student's grades/answers/category and the current session's reference data, calls `scoring.py`/`eligibility.py`, builds Best Fit, caches the result in `analysis`. Raises `MissingGeneralRequirementsError` if the session has no syarat am row for the student's category (Phase 5). Gates interest scoring (`interest_areas`, `likely_to_love`) on the interest test being fully (20/20) answered, forcing 0/empty until then (Phase 6, decision `0008`). `get_analysis_summary` (Phase 7) orchestrates `GET /me/analysis/summary`: reuses `get_analysis` for the "enough data" gate and the scores, checks/updates the cached `summary` column, and calls `ai_summary.generate_summary` -- never raises for an AI failure, always returns the `not_enough_data`/`ok`/`unavailable` shape |
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
| `backend/migrations/versions/96f63a9f3e5c_add_ai_summary_columns_to_analysis.py` | Seventh migration (Phase 7): adds 2 nullable columns, `summary` (Text) and `summary_computed_at` (DateTime), to the existing `analysis` table. No new table and no rows loaded -- see decision `0011` for why the summary rides on the same cache row instead of a new table |

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
| `GET` | `/me/interest-answers` | Yes | The logged-in student's saved interest-test answers so far, plus whether all 20 are answered (`complete`). Lets the client resume a part-finished test (Phase 6, decision `0008`) |
| `PUT` | `/me/interest-answers` | Yes | Merge/upsert (Phase 6, decision `0008`) the logged-in student's interest-test answers: updates or inserts only the payload's questions, leaving every other saved answer untouched. Rejects duplicate question ids, unknown question/option ids, or an option that doesn't belong to its question |
| `GET` | `/me/analysis` | Yes | The logged-in student's both charts, Likely to excel/love, Sweet spot, Best Fit (up to 3 programs per area, Eligible/Conditional only), category (A/B), and `interest_test_complete`. Cached until the student's results or answers change. Interest scores stay forced to 0/empty until the interest test is fully (20/20) answered (decision `0008`) |
| `GET` | `/me/analysis/summary` | Yes | The logged-in student's AI-written plain-English summary of their own scores (Phase 7). `status`: `not_enough_data` (interest test unfinished or no SPM results -- AI never called), `ok` (summary text, cached or fresh), or `unavailable` (AI failure/timeout/missing key -- never a `500`). Sent to OpenAI: only interest-area and subject-group names + scores (decision `0010`). Cached on the same `analysis` row as the charts, so it's invalidated together with them (decision `0006`, decision `0011`) |

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
| `interest_answers` | `id`, `user_id` (FK `users`, `ON DELETE CASCADE`), `question_id` (FK `interest_questions`), `chosen_option_id` (FK `interest_options`) | Added by migration `23947a34f766` (Phase 4). One row per (`user_id`, `question_id`) the student has answered -- unique on that pair. `PUT /me/interest-answers` merges/upserts each save's rows into what's already there (decision `0008`), so a partial (save-as-you-go) answer set is allowed and previously-saved answers are never dropped by a later, smaller save |
| `analysis` | `user_id` (FK `users`, `ON DELETE CASCADE`, **primary key** -- one row per user, not a surrogate `id`), `result` (JSONB, the full `GET /me/analysis` response), `computed_at` (its own real `DateTime`, redundant with `result["computed_at"]` so a caller can order/filter without parsing JSON), `summary` (Text, nullable -- the cached AI summary text), `summary_computed_at` (DateTime, nullable -- Phase 7) | Added by migration `3916bef04fb3` (Phase 5); `summary`/`summary_computed_at` added by migration `96f63a9f3e5c` (Phase 7, decision `0011`). A cache: the first `GET /me/analysis` after a change computes and saves a row here; later `GET`s are served from it unchanged. The AI summary is filled in lazily by the first `GET /me/analysis/summary` after that. `PUT /me/results` and `PUT /me/interest-answers` delete the student's whole row here -- charts and summary together -- on every successful save (decision `0006`), so neither ever goes stale |

## Client

| File | Purpose |
|---|---|
| `client/src/App.jsx` | Page frame (`Nav`, page, `Footer`), `ScrollToTop`, and routes for all pages plus a `*` route to `NotFound.jsx`, wrapped in `AuthContext` (Phase 6; frame and 404 route added Phase 8) |
| `client/src/index.css` | Tailwind import, the Poppins theme font, and shared style classes used by every page: `.container-page`, `.card`, `.btn` (+ `-primary`, `-secondary`, `-ghost`, `-danger`, `-danger-outline`, `-lg`, `-sm`), `.label`, `.input`, `.select`, `.hint`, `.field-error`, `.link`, `.bg-grid` (Phase 8) |
| `client/src/api.js` | Helper for backend calls, including the `GET`/`PUT /me/interest-answers` resume calls (Phase 6) and `getMyAnalysisSummary` for `GET /me/analysis/summary` (Phase 7) |
| `client/src/constants.js` | Shared constants: the real SPM grade list, the required-subject codes (BM, SJ) (Phase 6), and `SUBJECT_GROUPS`, the 7 subject groups copied from `backend/app/importer/subjects.py` so the "excel" chart can show every group, with N/A for empty ones (decision `0019`). Keep it in sync with the backend list |
| `client/src/programName.js` | `displayProgram()`: hides the `#` marker (it repeats the interview flag), turns "Baru" into a "New" badge, and shows the name in title case with Malay joining words lowercase; raw names stay in the data and search (decisions 0009, 0016) |
| `client/src/context/AuthContext.jsx` | Holds the access token in React state only (never `localStorage`/`sessionStorage`); does a silent `POST /auth/refresh` on app load with `credentials: "include"`; retries a failed call once via refresh, then routes to Login (Phase 6) |
| `client/src/components/ui.jsx` | Shared pieces every page reuses: `Icon` (inline SVG icons), `LogoMark`, `Logo`, `PageHeader`, `Alert` (success/warning/error/info), `Badge`, `ProgramFlags` (New/STEM/TVET/Bumiputera only/Interview badges), `Spinner`, `PageLoader`, `PageError` (Phase 8) |
| `client/src/components/Nav.jsx` | Sticky top menu on every page. Links change with login. Folds into a menu button below 768px wide (Phase 6; rebuilt Phase 8) |
| `client/src/components/Footer.jsx` | Site footer: logo, short description, links, e-Panduan data credit (Phase 8) |
| `client/src/components/AuthShell.jsx` | Two-panel layout shared by Log in and Register: brand panel on wide screens, form card on the right (Phase 8) |
| `client/src/components/ProtectedRoute.jsx` | Wraps a page; sends a logged-out visitor to Login instead of rendering it. Shows `PageLoader` while login is checked (Phase 6) |
| `client/src/components/RadarChartCard.jsx` | Reusable radar chart (Recharts). Each spoke shows the area name with its score underneath; scale numbers hidden (decision `0017`). Always renders a real `<table>` of the same numbers, hidden from view but read by screen readers (`sr-only`, not `display: none`, decision `0018`), for WCAG AA (Web Content Accessibility Guidelines, level AA) accessibility, plus empty states with a link to the missing step (Phase 6; `variant` excel/love colours and spoke labels added Phase 8) |
| `client/src/components/EligibilityBadge.jsx` | Shows a program's Eligible/Conditional/Not Eligible verdict with its plain-English reasons. Also exports `VerdictPill` and `ReasonList` separately, used by My Results (Phase 6; split Phase 8) |
| `client/src/components/AISummaryCard.jsx` | Fetches `GET /me/analysis/summary` on its own `useEffect`, independent of `MyResults.jsx`'s chart fetch, so a slow or failed AI call never blocks or delays the charts. Renders loading / `ok` / `not_enough_data` / `unavailable` states (Phase 7) |
| `client/src/pages/Home.jsx` | Landing page: headline, an example chart labelled "Example result", live program and university counts (from `GET /programs` and `GET /universities`), how it works, features, closing sign-up banner (Phase 8) |
| `client/src/pages/NotFound.jsx` | "Page not found" page for any unknown address, with links to Home and Explore (Phase 8) |
| `client/src/pages/Register.jsx` | Sign-up form; explains that race is collected only to check Bumiputera-only programs; collects consent (Phase 6) |
| `client/src/pages/Login.jsx` | Log-in form; shows the backend's generic wrong-credentials message; redirects to the page the student was headed to (Phase 6) |
| `client/src/pages/SpmResults.jsx` | SPM subject + grade rows; Bahasa Melayu and Sejarah always shown as required; grade choices limited to the real SPM grade list, backend stays authoritative (Phase 6) |
| `client/src/pages/InterestTest.jsx` | The 20 questions; loads saved progress on mount via `GET /me/interest-answers`; saves each answer immediately via the merge/upsert `PUT`; shows live "N of 20 answered" progress; resumes correctly after a reload (Phase 6, decision `0008`) |
| `client/src/pages/MyResults.jsx` | Mounts `AISummaryCard.jsx` (Phase 7) plus both radar charts with text-table fallbacks, Best Fit list with sweet-spot/likely-to-excel/likely-to-love badges, eligibility badges with reasons, and a "finish the interest test" empty state while `interest_test_complete` is `false` (Phase 6) |
| `client/src/pages/Explore.jsx` | Filter by interest area and university, plus free-text search; fetches `GET /programs` once and filters that list in the browser (client-side filtering) (Phase 6) |
| `client/src/pages/ProgramDetail.jsx` | Full program info, the original Malay rule text (`text_ms`), and an e-Panduan source-credit line (Phase 6) |
| `client/src/pages/Account.jsx` | Account info, log out, and a 2-step (checkbox-gated) delete-account confirmation (Phase 6) |

## Docker services

| Service | Port | What it does |
|---|---|---|
| `db` | 5432 | PostgreSQL 16, with a health check |
| `backend` | 8000 | Runs `uv run alembic upgrade head`, then the server with auto-reload |
| `client` | 5173 | Vite dev server |

## Wiring

- **Auto reload in development:** the backend (uvicorn `--reload --reload-dir app`) and the client (Vite `watch.usePolling`) both **poll** for file changes, because Docker on Windows does not pass file-change events into containers. The backend watches only `app/`, because the raw HTML files in `data/upu/.cache/` crashed its file watcher.

- **Start order:** `db` becomes healthy → `backend` runs migrations, then starts → `client` starts.
- **Routers:** each file in `backend/app/api/` exposes a `router`. `main.py` plugs it in with `app.include_router(...)`.
- **Settings:** every service reads the repo-root `.env`. The client reads `VITE_API_URL` to find the backend.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals behind these structures (T1, T2, T4, T5, T6, T7, T8) |
| `docs/prd/ui-redesign-prd.md` | Intent | Phase 8: why the client's shared pieces and new layouts exist |
| `docs/product-roadmap.md` | Roadmap | Which phase adds each *(planned)* item |
| `docs/decisions/NNNN-*.md` | Decision log | Structural changes that diverged from the plan |
