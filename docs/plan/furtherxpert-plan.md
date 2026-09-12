# FurtherXpert Implementation Plan

> **Quick summary**
> - **What:** how we build FurtherXpert, phase by phase. The PRD says *what* and *why*; this plan says *how*.
> - **Who uses it:** anyone building a phase. Read your phase's section here first, then the PRD's technical rules (T1–T8).
> - **Now:** Phases 1–2 are done (written up after the fact). Phases 3–7 are planned.
> - **If the build must differ from this plan:** don't edit the plan. Add a note in `docs/decisions/`.

> **Type:** Plan | **Must stay current:** No -- record divergences in decision log, rewrite only during re-planning

<!-- AI Context
Role: This document describes *how* to build the feature, not *what* or *why*.
Read the corresponding PRD first for intent and constraints, then use this plan
to guide implementation order, component boundaries, and technical decisions.
Do not rewrite this document during coding. If the implementation diverges from
this plan, add an entry to the decision log instead. Only rewrite during a
deliberate re-planning session.
Written 2026-09-12, after Phases 1–2 shipped; their sections record what was built.
-->

## Overview

The app has 3 parts that run together in Docker:
- a **backend** (the server, FastAPI),
- a **client** (the website, React),
- a **database** (PostgreSQL).

The heart of the app is the **rules engine**, the code that turns grades and test answers into charts, Best Fit and eligibility. Everything else feeds it data or shows its results.

## Technical Approach

1. **Rules are pure functions.** Scoring and eligibility are plain Python functions: data in, results out. They never touch the database, the network, or the clock. So they're fast to test and always give the same answer.
2. **Routers stay thin.** A **router** (the code that answers one kind of request) loads data, calls a service, and returns the result. No business rules live in routers.
3. **Reference data travels one way:** e-Panduan website → import script → saved **snapshot** file → Alembic **data migration** → database. Nobody edits reference rows by hand.
4. **The client only displays.** React never recalculates a score or eligibility.
5. **Results are cached.** `/me/analysis` saves its result in the `analysis` table. The cache is cleared when the student changes their results or test answers.
6. **The AI is optional.** The summary is a separate call. If it fails, nothing else breaks.

## System Components

| Component | Responsibility |
|---|---|
| `backend/app/api/` | Routers: turn HTTP requests into service calls |
| `backend/app/core/` | Settings, database connection, login tokens, rate limiting |
| `backend/app/models/` | Database tables |
| `backend/app/schemas/` | Shapes of request and response data |
| `backend/app/services/auth.py` | Sign-up and login rules (done) |
| `backend/app/services/scoring.py` | Subject groups, interest areas, Best Fit (Phase 5) |
| `backend/app/services/eligibility.py` | UPU check: syarat am + syarat khas (Phase 5) |
| `backend/app/services/analysis.py` | Loads data, runs scoring + eligibility, caches the result (Phase 5) |
| `backend/app/services/ai_summary.py` | GPT-5 summary from scores only (Phase 7) |
| `backend/app/importer/epanduan.py` | Reads e-Panduan and writes the snapshot (Phase 3) |
| `backend/data/upu/*.json` | Saved snapshots, committed to git (Phase 3) |
| `backend/migrations/` | Table changes and reference-data loads |
| `client/src/` | Pages, login state, charts (Phase 6) |

## Processing Flow

**A. The student's journey**
1. **Sign up and log in** (done). The browser holds a 15-minute access pass in memory, and a 7-day refresh cookie.
2. **Save SPM results** (`PUT /me/results`) and **interest answers** (`PUT /me/interest-answers`). Each save clears the cached analysis.
3. **Get the analysis** (`GET /me/analysis`):
   1. Load the student's grades, answers, citizenship, race and SPM year.
   2. Load reference data: subjects, groups, areas, programs and rules for the current session.
   3. Work out category A or B from the SPM year.
   4. Run scoring: group scores, area scores, excel and love lists.
   5. Run eligibility for every program. Each result is Eligible, Conditional or Not Eligible, with reasons.
   6. Build Best Fit: up to 3 programs per top area.
   7. Save the result in `analysis` and return it.
4. **The client draws** both spider charts, the text tables, and Best Fit.
5. **Get the summary** (`GET /me/analysis/summary`), a separate call. If it fails, the page shows "Summary unavailable".

**B. The yearly data import**
1. A developer runs the importer for the new session. It reads the program lists (categories A and B), then each program's rules.
2. The importer turns the Malay rule text into the rule tree. It lists anything it can't read in `unparsed`.
3. It writes `backend/data/upu/<session>.json`. A person reviews the `unparsed` list.
4. A new data migration loads the snapshot, replacing the old session.

## Dependencies

| Dependency | Purpose |
|---|---|
| FastAPI, Uvicorn | Backend web server |
| SQLAlchemy 2, psycopg | Talking to PostgreSQL |
| Alembic | Database migrations, including data loads |
| pydantic, pydantic-settings | Data shapes and `.env` settings |
| PyJWT, argon2, slowapi | Login tokens, password scrambling, rate limits |
| httpx, a HTML parser (for example selectolax or BeautifulSoup) | Importer: fetching and reading e-Panduan pages (Phase 3) |
| openai | GPT-5 summary (Phase 7) |
| pytest | Backend tests |
| React, React Router, Vite | Client app |
| Tailwind CSS v4 | Client styling |
| Recharts | Spider charts |

## Implementation Phases

Each phase runs: build → test → review → docs. A phase is done when its check passes (see `docs/product-roadmap.md`).

### Phase 1: Foundation (done)

- **Built:** Docker Compose, the backend skeleton (uv, FastAPI, SQLAlchemy, Alembic), the client skeleton (Vite, React, Tailwind, Recharts), and `/health`.
- **Check:** live `/health` reports `db: ok`.

### Phase 2: Accounts (done)

- **Built:** the `users` table, `/auth/*` and `/me` routes, JWT, argon2, and rate limits.
- **Check:** 14 tests pass on a separate test database (decision `0001`).

### Phase 3: Reference data

**Goal:** the official UPU data for sesi 2026/2027 is in the database, and the API can list it.

**Tasks:**
1. **Tables** (one migration): `sessions` (name, `latest_spm_year`), `universities`, `programs`, `campuses`, `subjects` (code, Malay name, English name, group, old-syllabus flag), `subject_groups`, `interest_areas` (NEC prefixes + subject groups, PRD T1), `general_requirements` (per session + category), `program_requirements` (per program + category; rule tree + original Malay text + `unparsed` flag).
2. **Subject list:** a hand-written list of SPM subjects, including old-syllabus ones. It maps every Malay name and "/" alternative found in e-Panduan to one subject code.
3. **Importer** (`backend/app/importer/epanduan.py`):
   - Fetch the list pages for A and B one at a time, with a short pause between requests.
   - Keep only UA diploma codes (`^U[A-Z]4`).
   - Read each program's details: name, university, NEC code, semesters, mode, flags, merit, campuses, careers.
   - Fetch each program's rules (`modalSyarat`, with header `X-Requested-With: XMLHttpRequest`).
   - Read the rules from the page's HTML structure: single-subject minimums, "one of these", "ATAU" choices, "N more subjects not yet counted", and the Bumiputera line.
   - Anything else goes to `unverifiable` (checked later as Conditional) or `unparsed`.
   - An unknown subject name **stops the import** with a clear error.
4. **Snapshot:** run the importer and commit `backend/data/upu/2026-2027.json`. Report how many programs were fully read.
5. **Data migration:** load the snapshot and replace all reference rows for the session.
6. **Routes:** `GET /subjects`, `GET /universities`, `GET /programs` (filter by area, university, text search), and `GET /programs/{code}` (with the original Malay rule text and source credit).

**Check:**
- Parser tests on saved real pages: `UE4481001` (A and B), `UP4481001` ("ATAU"), and one Bumiputera-only program.
- Every subject name in the snapshot maps to a subject.
- The migration loads the same program counts as the snapshot.
- The routes return the right data.

### Phase 4: Student input

**Goal:** students can save and reload their SPM results and interest-test answers.

**Tasks:**
1. **New interest test:** write 20 new questions, each with 4 answers + "None of the above". Each answer is tagged to **exactly one** of the 9 areas. Keep areas roughly balanced. **The questions are drafted in chat and approved by the product owner before seeding.**
2. **Tables:** `spm_results` (user, subject, grade), `interest_questions`, `interest_options` (with area), `interest_answers` (user, question, option). Student tables use `ON DELETE CASCADE` to `users`.
3. **Seed migration** for the approved questions.
4. **Routes:** `GET/PUT /me/results`, `GET /interest-test`, `PUT /me/interest-answers`.
   - Validate grades against the SPM grade list.
   - Require BM and Sejarah rows.
   - Reject unknown subjects.
   - Accept exactly one answer per question.

**Check:**
- Bad grades and unknown subjects are rejected.
- A retake replaces the old answers.
- A student can't touch another student's data.
- Deleting an account removes their results and answers.

### Phase 5: Rules engine

**Goal:** `GET /me/analysis` returns both charts' numbers, Best Fit and eligibility, exactly per PRD T1–T2.

**Tasks:**
1. `scoring.py`: grade points, group scores (hide empty groups), area scores (normalised), the excel and love lists, tie rules, Sweet spot.
2. `eligibility.py`: evaluate syarat am + syarat khas as one rule tree. Each subject counts **once**, using a **backtracking search** (try an assignment, undo it if it fails, try the next).
   - Check order: citizenship → Bumiputera → grades → Conditional flags.
   - Return reasons in plain English.
3. `analysis.py`: load data, run both, build Best Fit, and cache the result in `analysis`. Saving results or answers clears the cache.
4. **Golden tests:** 6 sample students (see the `proj-furtherxpert-rules` skill) with fixed expected outputs.

**Check:**
- Golden tests pass.
- The "counts once" trap test passes.
- Eligibility matches e-Panduan for the test programs.

### Phase 6: Client pages

**Goal:** every page in PRD T7 works end to end.

**Tasks:**
1. **Login state:** a React context keeps the access token in memory only. On page load, it calls `/auth/refresh` to get a new token. It retries once on a 401 (**401** = "not logged in" error).
2. **Pages:** Register (with the race explanation), Login, SPM Results, Interest Test, My Results, Explore, Program Detail, Account (with delete).
3. **Charts:** a Recharts spider chart for subject groups and one for interest areas. Each also has a text-table version.
4. **Best Fit cards:** the excel and love lists, the Sweet spot tag, programs with eligibility badges and reasons.
5. **Explore:** filters by area and university, and program detail with the Malay rule text and source credit.

**Check:**
- `npm run build` passes.
- A click-through by hand of the whole journey works.
- Charts show their text tables.

### Phase 7: AI summary

**Goal:** a short, safe plain-words summary.

**Tasks:**
1. `ai_summary.py`: send GPT-5 **only** area names + scores and group names + scores. Keep it to 120 words or fewer, with a time limit.
2. `GET /me/analysis/summary` caches the summary with the analysis.
3. The client shows the summary, or "Summary unavailable" if it fails.

**Check:**
- A test proves the AI request carries no email, race or grades.
- A forced AI failure still returns charts.
- The summary arrives in under 10 seconds.

## Testing Strategy

- **Unit tests** check the pure functions (scoring, eligibility, the importer's parser) using fixed inputs. The parser uses saved real e-Panduan HTML pages in `backend/tests/fixtures/`.
- **Golden tests** use 6 sample students with fixed expected outputs. Expected values only change for an intended rule change, and the change note says why.
- **API tests** run against a separate PostgreSQL test database (decision `0001`).
- **The client** must build (`npm run build`). Each phase's screens get a click-through by hand.
- **Every phase** keeps all earlier tests passing.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| KPT changes the e-Panduan website | The importer stops working | The committed snapshot keeps the app working. Fix the importer next import season |
| Malay rule text is irregular | Some programs can't be checked automatically | List them in `unparsed`, show them as Conditional with the raw text, and report coverage |
| A subject name appears that we don't know | Wrong eligibility | The import stops with a clear error instead of guessing |
| UPU rules change between years | Stale eligibility | A yearly import replaces the whole session. The source and session are shown in the UI |
| The area mapping is wrong | Poor Best Fit | Counsellor review (PRD open question) |
| The dev PC is low on memory | Docker or git crashes | Run heavy tasks one at a time. Cap Docker's memory if needed |
| Too many requests to KPT's server | Being blocked, or rude load | Fetch one page at a time, with pauses. Only run it once per season |

## Roadmap Phase

**Phase:** Phases 1–7 in `docs/product-roadmap.md`.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/product-roadmap.md` | Roadmap | Phase order, status, and checks |
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals and exact rules (T1–T8) this plan builds |
| `docs/furtherxpert-workflow.md` | Workflow | How the system behaves today |
| `docs/reference/folder-structure.md` | Reference | Where each component's files live |
| `docs/decisions/NNNN-*.md` | Decision log | Divergences from this plan |

## Open Questions

- [ ] The 20 new interest questions: draft them in chat before Phase 4 starts.
- [ ] Which HTML parser should the importer use? The builder picks one in Phase 3 and records the choice in a decision entry.
