# FurtherXpert Workflow

> **Quick summary**
> - **What:** how the app behaves **today**: what happens, step by step, when a student uses it.
> - **Why:** when you change code, this doc is the spec for current behaviour. If code and this doc disagree, fix one of them.
> - **Now covers:** accounts (sign up, log in, refresh, log out, view and delete account), reference data (the yearly import, plus the subject/university/program lookup routes), student input (saving SPM results, taking or retaking the interest test, reading your own data back, and resuming a part-finished interest test), analysis (Phase 5: the 2 charts, Best Fit, and eligibility, cached and recomputed only when the student's data changes, and gated on the interest test being fully answered), the client pages (Phase 6: the 8 screens a student actually sees and clicks through, from registering to deleting their account), and the AI summary (Phase 7: a short plain-English summary of a student's own charts, built from scores only, cached alongside the charts, and loaded separately so it never blocks or delays them). Phase 7 is the final phase of the first release, so the flows below cover the full build. Phase 8 (UI redesign) then gave every page a new look, without changing what the pages do or which API calls they make (Flow 5).

> **Type:** Workflow | **Must stay current:** Yes -- update when behavior changes

<!-- AI Context
Role: This document describes how the system behaves *today*.
Use it as the authoritative source for current processing flows, stage
sequencing, error handling, and runtime defaults. When writing or modifying
code, the behavior described here is the specification.
This document must be updated before a coding session ends whenever behavior,
flow, or error handling changes. If it conflicts with a PRD or plan, this
document reflects reality; record the divergence in the decision log.
Add one "Flow" section per feature as phases ship.
-->

## Purpose

Describes the live flows of FurtherXpert. That's the **accounts flow** (Phase 2), **reference data** (Phase 3), **student input** (Phase 4), **analysis** (Phase 5), the **client pages** (Phase 6), and the **AI summary** (Phase 7). Flows 1-4 and 6 below start from API requests directly, since that's how a developer or a test checks them. Flow 5 covers the same ground from the student's point of view: what they see and click on the website, and which of the other flows' API calls each screen makes.

## Trigger

A request to the backend (`http://localhost:8000` in development).

## Preconditions

- Docker Compose is running: `db` is healthy, and `backend` has run `alembic upgrade head`.
- The `.env` file has `JWT_SECRET` set. The backend refuses to start without it.

## Flow 1: Accounts

### 1. Sign up

**Input:** `POST /auth/register` with email, password, `is_citizen`, `race`, `spm_year`, and consent.
**Actions:**
1. Check the data:
   - the password has at least 8 characters,
   - race is one of the 7 allowed values,
   - `spm_year` is between 1970 and this year,
   - consent is given.
2. Lower-case the email.
3. Scramble the password with argon2 (**hashing**, which can't be reversed).
4. Save the new row in `users`, with `consent_at` set to now.

**Output:** `201 Created` with the public account details. The password hash is never returned.
**On failure:** `422` if the data is invalid. `409` "Email already registered" if the email is taken. `429` after 5 tries in 1 minute from the same IP address.

### 2. Log in

**Input:** `POST /auth/login` with email + password.
**Actions:**
1. Look up the lower-cased email.
2. Check the password.
   - If the email doesn't exist, it still checks against a dummy hash. So the response takes the same time either way, and an attacker can't tell which emails exist.
3. Create an **access token** (a signed login pass, valid 15 minutes) and a **refresh token** (valid 7 days).

**Output:** `200` with `access_token` in the body. The refresh token is set as a cookie: `refresh_token`, `httpOnly`, `Secure`, `SameSite=Strict`, `Path=/auth`.
**On failure:** `401` "Wrong email or password", the same message for either mistake. `429` after 5 tries in 1 minute.

### 3. Use the app while logged in

**Input:** any `/me` request, with the header `Authorization: Bearer <access_token>`.
**Actions:**
1. Check the token's signature and expiry, and that its type is `access`.
2. Load the user from the token's user id. **Never** from an id in the request.

**Output:** the request runs for that user only.
**On failure:** `401` "Invalid or expired token", if the token is missing, expired or the wrong type, or the user no longer exists.

### 4. Refresh the access token

**Input:** `POST /auth/refresh`. The browser sends the `refresh_token` cookie automatically.
**Actions:** check the cookie token's signature, expiry, and type (`refresh`). Then issue a new 15-minute access token.
**Output:** `200` with a new `access_token`.
**On failure:** `401` "Missing refresh token" or "Invalid or expired token".

### 5. Log out

**Input:** `POST /auth/logout`.
**Actions:** delete the refresh cookie. The client should also forget its access token.
**Output:** `200` `{"detail": "logged out"}`.

> **Watch out:** the server is **stateless**, meaning it keeps no list of logged-in users. So an access token copied before logout still works until it expires, at most 15 minutes.

### 6. View or delete my account

- **`GET /me`** returns the logged-in student's account (no password hash).
- **`DELETE /me`** deletes the logged-in student's row, and returns `204 No Content`. Later student tables will delete their rows automatically with it (`ON DELETE CASCADE`).

## Flow 2: Reference data

Reference data is the official list of subjects, universities, and diploma programs, taken from UPU's own **e-Panduan** website. It's loaded once a year, then the app reads it many times.

### 1. Yearly import (a developer runs this by hand, not a student action)

**Input:** running the importer script, `backend/app/importer/epanduan.py`, with a `--session` flag (for example `2026/2027`).
**Actions:**
1. Fetch the e-Panduan program-list pages for category A and category B, one page at a time, waiting at least 1 second between requests. This is deliberately slow (**polite crawling**) so it doesn't overload UPU's site.
2. For each program, fetch its detail page and its rule fragment (a pop-up the site loads in the background, called an **AJAX** call).
3. Save every raw page under `backend/data/upu/.cache/` as it's fetched. This is a **resume cache**: if the import stops partway (network error, PC restart), re-running it skips pages already saved instead of re-fetching everything.
4. Turn the Malay entry-rule text into a structured **rule tree** the app can check automatically later (single-subject minimums, "one of these" choices, "ATAU" = "OR" choices, Bumiputera-only flags). Anything it can't confidently read is listed under `unparsed` instead of guessed.
5. Write the result to a **snapshot** file, `backend/data/upu/<session>.json` -- for example `2026-2027.json`.
6. A person reviews the `unparsed` list before the snapshot is trusted.
7. A database **migration** (a script that changes the database's layout or loads data) reads the snapshot and loads it into the database.

**Output:** the `sessions`, `universities`, `programs`, `campuses`, `subjects`, `subject_groups`, `interest_areas`, `general_requirements`, and `program_requirements` tables are filled for that session.
**On failure:** an unknown subject name (one not in the hand-written subject list) **stops the import immediately** with a clear error -- it never guesses a subject.

> **Watch out:** re-running the data migration for the same session **deletes and reloads** that session's programs, campuses, and requirement rows. Other sessions, and the shared subject/university lists, are left alone.

> **Watch out:** `backend/data/upu/.cache/` can hold hundreds of raw HTML files. It's gitignored and never committed -- only the finished `.json` snapshot is.

### 2. Look up subjects, universities, and programs

These 4 routes are **public** -- no login needed, because they're just lookup lists, not personal student data.

- **`GET /subjects`** -- every SPM subject: code, Malay name, English name, subject group, and whether it's an old-syllabus subject (one no longer taught, but older SPM holders may still have it).
- **`GET /universities`** -- every public university's code (for example `UE`) and full name.
- **`GET /programs`** -- every diploma program in the most recently loaded session. Optional filters, combined with AND:
  - `area` -- an interest area name (for example `Science & Technology`).
  - `university` -- a university code (for example `UE`).
  - `q` -- free-text search, case-insensitive, matched against the program name.
  Each result has: code, name, university, subject area, study level, study mode, duration, average merit score, campuses, and flags (`stem`, `tvet`, `bumiputera_only`, `interview`).
- **`GET /programs/{code}`** -- one program's full detail: everything in the list result, plus its career paths, its entry-rule tree for both categories, the original Malay rule text, and a source credit line (for example "Source: e-Panduan UPU, KPT, sesi 2026/2027").
  - **On failure:** `404` "Program not found" if the code doesn't exist in the current session.

## Flow 3: Student input

Student input is the SPM (**Sijil Pelajaran Malaysia**, Malaysia's high-school leaving exam) results a student enters by hand, and their answers to the 40-question interest test. Both are personal data, so every route in this flow needs a login, and each route only ever touches the logged-in student's own rows -- the same rule as Flow 1's `/me` routes.

### 1. Save SPM results

**Input:** `PUT /me/results` with a list of `{subject_code, grade}` pairs.
**Actions:**
1. Check each grade is one of the 10 real SPM grades: `A+ A A- B+ B C+ C D E G`. There's no `B-`, `C-`, or `F`.
2. Check the payload has no repeated subject code.
3. Check Bahasa Melayu (`BM`) and Sejarah (`SJ`) are both in the payload -- the official entry rules (**syarat am**, general requirements) always need both, so every save must include them.
4. Check every subject code is a real one from `GET /subjects`.
5. **Upsert** each row: update the grade if the student already saved that subject, insert a new row otherwise. A save never deletes a subject the payload leaves out -- so a student can top up their results over several saves without re-typing everything each time.

**Output:** `200` with the student's full, current results list (subject code, both subject names, grade), sorted by subject name.
**On failure:** `400` with a message naming the problem -- a bad grade, a duplicate subject in the payload, a missing `BM`/`SJ` row, or an unknown subject code.

### 2. Read your own SPM results

**Input:** `GET /me/results`.
**Output:** `200` with the same list shape as above -- every subject the student has saved so far, or an empty list if none yet.

### 3. Take or retake the interest test

**Input:** `GET /me/interest-test` (Phase 9, rotation PRD T2). Returns the student's own current **set**: 40 questions from the 300-question bank, in display order. Each question has its options' text and id only -- **never** which interest area an option counts toward. That's on purpose: knowing the mapping would let a student game their own score. The response also carries the saved answers, `answered`, `total`, `complete`, and `has_finished_set` (true when an earlier finished set still feeds My Results).
**Actions:**
1. Lock the student's row, so two tabs opening at once can't create two sets.
2. **No set yet, or the latest set is finished:** draw a new set (`services/question_sets.py`, decision `0020`). It is balanced (every area in 16–20 of the 40 questions) and uses questions the student has never been given. Only when fewer than 40 unseen questions are left does it top up with questions seen longest ago, never from the most recent set.
3. **Latest set is unfinished:** return it unchanged, with its saved answers, so the student resumes.

**Input:** `POST /me/interest-test/rotate` (Phase 9).
**Actions:** if the latest set is unfinished, mark it discarded and delete its answers. Its question list stays, as "seen" history. Then draw a new set, clear the cached analysis, and return the new set in the same shape as above. A finished set's results are never touched.

**Input:** `PUT /me/interest-answers` with a list of `{question_id, option_id}` pairs.
**Actions:**
1. Check the payload has no repeated question id, and every question id and option id is real.
2. Check each option actually belongs to the question it's paired with -- a mismatched pair (option from a different question) is rejected. Also check every question is in the student's **current set** (Phase 9). A question outside it, or any answer before a set exists, is rejected.
3. **Merge/upsert (decision `0008`), not a full replace:** each payload item updates the student's existing answer for that question in the current set, or inserts a new one. A question the payload leaves out keeps whatever the student answered before -- it's never deleted. This is what lets the client save progress after every single question (Phase 6 "save-as-you-go") without resending everything so far.
4. A payload doesn't have to cover all 40 questions -- only the questions it mentions are touched. When the set's 40th answer is saved, the set is marked finished (`completed_at`), and the answers of any older set are deleted: only the newest finished set's answers are kept (rotation PRD section 6). Interest scores only ever come from the latest finished set (decision `0008`, see Flow 4 step 1g2).

**Output:** `200` with the saved `{question_id, option_id}` pairs (only the ones in this payload, not the student's full answer set).
**On failure:** `400` with a message naming the problem -- a duplicate question id, an unknown question or option id, an option that doesn't belong to its question, or a question that isn't in the current set.

**Input:** `GET /me/interest-answers` (Phase 6, decision `0008`).
**Actions:** load the answers saved for the student's current set. It never creates a set.
**Output:** `200` with `{"answers": [{question_id, option_id}, ...], "complete": bool}` -- the current set's saved answers (however many so far), and whether all 40 are answered yet. The Interest Test page uses `GET /me/interest-test` instead, which returns the questions and answers together.

### 4. Deleting your account cleans up both

`DELETE /me` (Flow 1) removes the student's `spm_results`, `interest_test_sets` (with their question lists), and `interest_answers` rows automatically, the same way it will for every future student table: the tables point back at `users` with `ON DELETE CASCADE`, so the database removes them as part of deleting the account row -- no extra clean-up code needed.

> **Watch out:** `spm_results` and `interest_answers` are keyed to a login, not a name or email. So even the student who "owns" the data can only reach it through their own access token -- there's no route that takes another student's id.

## Flow 4: Analysis

Analysis turns a student's saved SPM (**Sijil Pelajaran Malaysia**) results and interest-test answers into the 2 charts, the **Best Fit** list (up to 3 matching programs per area), and an eligibility verdict for every program in the student's UPU category. It's personal data, so like Flow 3 it needs a login, and only ever touches the logged-in student's own rows.

### 1. Get your charts, Best Fit, and eligibility

**Input:** `GET /me/analysis`.
**Actions:**
1. Look for an existing cached row for this student in the `analysis` table. If one exists, return it as-is -- skip every step below.
2. If there's no cached row, compute fresh:
   a. Load the student's saved `{subject_code: grade}` pairs, and the subject-group each subject belongs to.
   b. Work out **category A or B**: compare the student's `spm_year` to the most recently loaded session's `latest_spm_year`. Same year = category A (this year's SPM leavers); older = category B.
   c. Load the 9 interest areas. Find the student's latest **finished** interest test set, and how many of **that set's** 40 questions can award each area a point (its "max picks", rotation PRD T1).
   d. Count the student's own picks per area from that set's answers ("None of the above" answers don't count toward any area).
   e. Load **syarat am** (general_requirements), the entry rules that apply to every program in this session + category.
   f. Load every program in this session + category, with its own **syarat khas** (program_requirements), and run the eligibility check (Flow 4 step 2's rules) for each one against the student's grades, citizenship, and race.
   g2. **Interest-test completeness gate (decision `0008`, per set since Phase 9):** interest scores are only ever computed from a fully answered (40/40) set. With no finished set, every Chart 2 score is forced to 0 -- a part-finished test's picks so far must never leak into the chart, Best Fit, or a sweet spot. A part-finished newer set never changes the chart: the latest finished set's scores stay until the new set is finished.
   g. Compute **Chart 1** (subject-group scores: the mean grade-percent of the subjects the student took in that group; a group with none of its subjects taken is left out entirely, never shown as 0), and **Chart 2** (interest-area scores: picks / max picks, as a percent, only once the interest test is complete -- otherwise every one of the 9 areas is shown at a forced 0%; the 9 areas are always shown either way, never omitted).
   h. Compute **Likely to excel** (top 3 areas by Chart 1's related subject groups; an area is left out if the student has none of its subject groups) and **Likely to love** (top 3 areas by Chart 2's score, **excluding any area that scores 0 interest** -- see decision `0007` -- and forced to empty entirely while the interest test is incomplete -- decision `0008`). Ties are broken by the other list's score, then by area name. Because 0-score areas are excluded, Likely to love can return 0 to 3 areas -- fewer than 3, or empty if the student hasn't taken the interest test, hasn't finished it yet, or picked "None of the above" every time.
   i. **Sweet spot:** any area that appears in both top-3 lists. Since Likely to love can no longer contain a 0-score area, a 0-score area can no longer be a Sweet spot either -- a direct consequence of step h's rule, not a separate check.
   j. **Best Fit:** for every area that appears in *either* top-3 list (the union, not excel-only), show up to 3 of that area's programs -- Eligible ones first, then by name, and only Eligible or Conditional programs, never Not Eligible.
   k. Save the whole result as one row in `analysis` (replacing nothing, since there's no existing row at this point), and return it.

**Output:** `200` with subject-group scores, interest-area scores, Likely to excel, Likely to love, Sweet spot, Best Fit, the category (A/B) used, `computed_at` (when it was worked out), and `interest_test_complete` (whether the student has a fully answered 40-question set -- decision `0008`).
**On failure:** if the current session has no `general_requirements` row for the student's category (a data problem, not a student mistake -- see the Error States table below), the request fails with a `500` server error rather than a normal eligibility result.

> **Watch out:** a non-citizen student still gets both full charts (PRD T2: "the charts are still shown") -- only Best Fit's program lists come back empty for them, since a non-citizen can never be Eligible or Conditional for any program (a hard stop, checked first). The same "still show charts" rule applies to a Bumiputera-only program mismatch: it only empties that one program out of Best Fit, not the whole response.

> **Watch out:** the eligibility verdict order is fixed. 1) not a citizen -> Not Eligible. 2) the program is Bumiputera-only and the student isn't -> Not Eligible. 3) the combined syarat am + syarat khas grade rules aren't met -> Not Eligible, with plain-English reasons (for example "Needs C in Matematik — you have D"). 4) an interview/test is needed, or a rule can't be checked automatically (medical, colour-blindness, age) -> Conditional, with reasons. 5) otherwise -> Eligible. Each of the student's subjects can satisfy at most one rule clause across syarat am and syarat khas combined -- see decision `0005` for how that's checked.

### 2. The cache, and when it goes stale

**How it works:** `analysis` holds at most one row per student. The first `GET /me/analysis` after a change computes fresh and saves it; every `GET` after that, until something changes, is served straight from that saved row -- same `computed_at` each time, no recompute.

**Cache invalidation:** both `PUT /me/results` (Flow 3) and `PUT /me/interest-answers` (Flow 3) delete the student's cached `analysis` row as part of their own save, every time they succeed -- there's no check for whether the save actually changed anything. So the very next `GET /me/analysis` after either save always recomputes fresh; it can never return numbers from before that save. See decision `0006` for why this is unconditional rather than diffed.

> **Watch out:** deleting a student's account (Flow 1's `DELETE /me`) removes their `analysis` row too, the same `ON DELETE CASCADE` way as `spm_results` and `interest_answers`.

## Flow 5: Client pages

The client is the website a student actually uses (`client/src/`, React + Vite + Tailwind CSS + Recharts, a charting library). It has 8 main pages, plus a Home page and a "Page not found" page. Every page that needs a login is wrapped in `ProtectedRoute.jsx`, which sends a logged-out visitor to Login instead of showing the page. None of these pages invent new rules -- each one just calls the API routes from Flows 1-4 and shows the result.

**Shared frame (Phase 8):** every page sits between a top menu (`components/Nav.jsx`) and a footer (`components/Footer.jsx`).
- The top menu stays pinned while scrolling. Below 768px wide it folds into a menu button.
- Its links change with login: logged out shows Explore, Log in and Get started; logged in shows My results, SPM results, Interest test, Explore and Account.
- Opening a new page jumps back to the top.
- An address that doesn't exist shows `pages/NotFound.jsx`, with links back to Home and Explore.
- While a page loads it shows a spinner; if loading fails it shows a red error box. Both come from `components/ui.jsx`.
- Program names show in title case everywhere, for example "Diploma Analisis Pelaburan" (decision `0016`).

**Home page:** `pages/Home.jsx`. Shows a headline, an example spider chart labelled "Example result" (made-up numbers, never a real student's), how it works, and features. It calls `GET /programs` and `GET /universities` (Flow 2 step 2) only to show live counts; if either fails, the counts are simply left out. Its buttons change with login.

### 1. Register

**Page:** `pages/Register.jsx`.
**What it does:** shows a form for email, password, citizenship (a Yes/No toggle), race, SPM year, and a consent tick. It explains in plain words that **race** is only collected to check Bumiputera-only programs (a UPU rule, not the app's choice). On wide screens, Register and Log in share a two-panel layout (`components/AuthShell.jsx`).
**Calls:** `POST /auth/register` (Flow 1 step 1).
**On failure:** shows the field error the backend returns (bad password length, unknown race, missing consent) or "Email already registered" and a link to Login.

### 2. Log in

**Page:** `pages/Login.jsx`.
**What it does:** shows an email + password form.
**Calls:** `POST /auth/login` (Flow 1 step 2). On success, saves the returned access token in memory (see step 3) and sends the student to the page they were originally headed to, or to My Results by default.
**On failure:** shows the same generic "wrong email or password" message the backend returns either way -- the page never guesses which part was wrong.

### 3. Staying logged in

**Piece:** `context/AuthContext.jsx`, used by every other page.
**What it does:**
1. Holds the access token only in React state (in-memory), never in `localStorage` or `sessionStorage` -- so it disappears if the tab is closed, matching the token-storage rule already set in the PRD.
2. On every app load, silently calls `POST /auth/refresh` (Flow 1 step 4) with `credentials: "include"` (so the browser sends the `refresh_token` cookie automatically) to get a fresh access token without the student having to log in again, as long as their refresh cookie is still valid.
3. If any API call comes back `401 Unauthorized`, tries `POST /auth/refresh` once and repeats the call. If that also fails, sends the student to Login.

### 4. SPM Results page

**Page:** `pages/SpmResults.jsx`.
**What it does:** shows one row per subject (subject + grade dropdown), with Bahasa Melayu and Sejarah always present since they're required (Flow 3 step 1). Grade choices are limited to the 10 real SPM grades from `constants.js`, but the backend is still the final judge -- the page never assumes its own copy of the rules is complete.
**Save bar:** the Save button stays disabled until Bahasa Melayu and Sejarah are added and every subject has a grade. A hint next to it says what's still missing, for example "Pick a grade for 2 more subjects."
**Calls:** `GET /me/results` on load, `PUT /me/results` on save (Flow 3 steps 1-2).
**On failure:** shows the backend's field error (bad grade, duplicate subject, missing BM/SJ, unknown subject code) without saving.

### 5. Interest Test page

**Page:** `pages/InterestTest.jsx`.
**What it does:** shows the student's 40-question set as a list of cards. Each option is a tile the student clicks; a picked tile is highlighted.
1. On load, calls `GET /me/interest-test` (Flow 3 step 3) once. It returns the set's questions and any answers already saved, so the student resumes exactly where they left off -- including after closing the tab and coming back later. If the last set was finished, this gives a new set, and an info note says the last results stay on My Results until this set is finished.
2. Saves each answer immediately after the student picks it, with `PUT /me/interest-answers` sending just that one `{question_id, option_id}` pair. Because that route merges/upserts (decision `0008`) instead of replacing everything, earlier answers are never lost by a later, smaller save.
3. Shows a live "N of 40 answered" count, a progress bar, and a **Get new questions** button, all pinned just under the top menu while scrolling. Once all 40 are answered, a "You've answered every question" card links to My Results.
4. **Get new questions** calls `POST /me/interest-test/rotate`. With no answers yet, or a finished set, it swaps right away. Otherwise an inline confirm asks first ("This clears your N answers…"), with "Get new questions" and "Keep these" buttons.
**Resume/completeness rule:** a set only counts as finished once all 40 questions have an answer across every save so far -- there's no separate "submit" step. Until the student has a finished set, `GET /me/analysis` (Flow 4 step 1g2) forces the interest-area chart and Likely to love to empty/0, so the My Results page (step 6 below) shows an unfinished state rather than a misleading partial score.

### 6. My Results page

**Page:** `pages/MyResults.jsx`.
**What it does:** the main results screen. Shows the AI summary via `components/AISummaryCard.jsx` (Phase 7, Flow 6), both radar charts (subject-group scores and interest-area scores) via the shared `components/RadarChartCard.jsx`, the Best Fit program list with sweet-spot / likely-to-excel / likely-to-love badges, and an eligibility badge with reasons for each program, via `components/EligibilityBadge.jsx`.
**Calls:** `GET /me/analysis` (Flow 4 step 1) for the charts and Best Fit, plus its own independent `GET /me/analysis/summary` call (Flow 6) for the AI summary -- the two calls run in parallel, not one after the other, so a slow or failed summary never delays the charts.
**Setup checklist:** if the student has no SPM results yet, or hasn't finished the interest test, a "Finish setting up" card shows both steps, ticked or linked.
**Chart labels:** each spoke of a chart shows the area name, with its score underneath. The chart's 0–100 scale numbers are hidden. Long names split onto 2 lines (decision `0017`).
**All 7 subject groups:** once any SPM results are saved, the "excel" chart always shows all 7 subject groups. A group the student took no subjects in shows "N/A" in grey, with no dot. `GET /me/analysis` itself still only returns the groups the student took; the page fills in the rest from `SUBJECT_GROUPS` in `constants.js` (decision `0019`).
**Accessibility fallback:** every radar chart also renders a real `<table>` of the same numbers that's hidden from view but kept in the page for screen readers (Tailwind's `sr-only`, not `display: none`), so a student using a screen reader still gets the same information. There's no visible "View as a table" toggle (decision `0018`). This meets **WCAG AA** (Web Content Accessibility Guidelines, level AA -- a common accessibility standard).
**Incomplete interest test:** while `interest_test_complete` is `false` (decision `0008`), the interest-area chart and Likely to love area show an empty state telling the student to finish the interest test, instead of a chart that looks real but isn't.

### 7. Explore page

**Page:** `pages/Explore.jsx`.
**What it does:** lets a student browse every diploma program, not just their own Best Fit, with filters by interest area and university plus free-text search. Programs show as cards. When any filter is set, a "Clear filters" button appears. If nothing matches, the page says so and offers to clear the filters.
**Calls:** `GET /programs` once on load (Flow 2 step 2), with no filter parameters, then filters that one fetched list in the browser (**client-side filtering**) as the student changes the area/university/search fields, instead of re-calling the API on every keystroke. With the current session's program count (166 category-A programs), fetching once and filtering locally keeps the page responsive without extra round trips to the server.

### 8. Program Detail page

**Page:** `pages/ProgramDetail.jsx`.
**What it does:** shows one program's full detail: everything from the Explore list, plus campuses, career paths, the original Malay rule text (`text_ms`), and a source-credit line crediting e-Panduan.
- Entry rules show one UPU category at a time, with Category A / Category B tabs. Each tab shows the general rules (syarat am) and the program rules (syarat khas).
- A rule with no text shows "No extra requirements listed for this category" instead of an empty box.
- A side panel asks "Do you qualify?" and links to My Results when logged in, or to Register when logged out.
**Calls:** `GET /programs/{code}` (Flow 2 step 2).
**On failure:** shows a "program not found" message on a `404`.

### 9. Account page

**Page:** `pages/Account.jsx`.
**What it does:** shows the logged-in student's own account details, a log-out button, and a delete-account control.
**Calls:** `GET /me` on load, `POST /auth/logout` for log out, `DELETE /me` for delete (Flow 1 steps 5-6).
**Safety check:** deleting the account needs 2 steps -- ticking a confirmation checkbox before the delete button is enabled -- so a stray click can't erase an account by accident. The backend still does the real work: cascading the delete to `spm_results`, `interest_answers`, and `analysis` (Flow 3 step 4, Flow 4's cache note).

## Flow 6: AI summary

The AI summary is a short, plain-English paragraph describing a student's own scores, written by GPT-5 (OpenAI's model). It's personal in the sense that it's about one student, but the data sent to GPT-5 is deliberately stripped down first -- see the privacy boundary below. Like Flow 4, it needs a login and only ever touches the logged-in student's own rows.

### 1. Get your summary

**Input:** `GET /me/analysis/summary`.
**Actions:**
1. Run `GET /me/analysis` (Flow 4 step 1) first, cached or fresh as usual. This is how the route gets both its "is there enough data" check and the exact scores the summary is built from -- it never queries the student's grades or interest answers itself.
2. **Not-enough-data check:** if the interest test isn't finished yet (`interest_test_complete` is `false`, decision `0008`) or the student has saved no SPM results yet (empty `subject_groups`), stop here. No call to GPT-5 is made.
3. **Cache check:** if the student's `analysis` row already has a saved `summary`, return it as-is -- skip every step below, the same cache-first pattern as Flow 4 step 1.
4. **Build the AI request:** take only the interest-area names + scores and subject-group names + scores from the just-computed analysis, and send **only** those to GPT-5 (`backend/app/services/ai_summary.py`). See "Privacy boundary" below for exactly what this excludes.
5. **Call GPT-5** with a 6-second hard timeout and no automatic retries (so one slow attempt can't quietly turn into several).
6. **Enforce the word limit in code**, not just by asking the model nicely: the reply is cut to 120 words or fewer, preferring to cut at the end of a full sentence rather than mid-sentence. This exists because a live check against the real OpenAI API once got a 122-word reply back despite the prompt asking for 120 words or fewer (decision `0013`).
7. Save the trimmed summary text onto the student's existing `analysis` row (the same row Flow 4 caches charts in), and return it.

**Output:** `200` with one of 3 states:
- `{"status": "not_enough_data", "summary": null, "message": "..."}` -- the interest test isn't finished, no SPM results are saved, or both. `message` says which.
- `{"status": "ok", "summary": "...", "message": null}` -- a summary is ready, cached or freshly generated.
- `{"status": "unavailable", "summary": null, "message": "Summary unavailable right now. Please try again later."}` -- GPT-5 failed, timed out, or no API key is configured. The real error is never shown to the student.

**On failure:** this route **never returns a `500`**. Any problem calling GPT-5 (missing/placeholder API key, timeout, or any other OpenAI error) is caught and turned into the `"unavailable"` state instead -- see "Watch out" below.

### 2. Privacy boundary: what does and doesn't reach GPT-5

**What's sent:** only interest-area names + scores (for example "Science & Technology: 62%") and subject-group names + scores (for example "Sciences: 78%") -- the same numbers already shown on the student's own charts.

**What's never sent:** email, race, citizenship, raw SPM grades (letters like `A+`), the student's user id, name, or any program/eligibility data. The system prompt also tells GPT-5 it has none of this and must never invent or assume it -- for example, it must never name a specific program or say the student is "eligible" for anything, since it has no eligibility data at all.

**Tone:** GPT-5 only receives the student's **top 3 subject groups** and **top 3 non-zero interest areas**, and the prompt asks for a warm, supportive summary. So it can't list what the student isn't into (decision `0014`). The charts still show every score.

> **Watch out:** this isn't just a stated intent -- it's checked by an automated test (`backend/tests/test_ai_summary.py`) that inspects the *exact* outgoing request kwargs sent to the (mocked) OpenAI client, not just the code that builds them. See decision `0010`.

### 3. Caching and invalidation: shares Flow 4's cache, for free

The summary is **not** a separate cache. It's 2 new nullable columns (`summary`, `summary_computed_at`) on the same per-student `analysis` row Flow 4 already caches charts in (decision `0011`).

That means the summary automatically inherits Flow 4's existing cache rule (decision `0006`): `PUT /me/results` and `PUT /me/interest-answers` (Flow 3) both delete the student's whole `analysis` row -- charts **and** summary together -- on every successful save. So the very next `GET /me/analysis` recomputes fresh charts, and the very next `GET /me/analysis/summary` after that always generates a fresh summary from the new scores. There's no separate invalidation logic to keep in sync with Flow 4's.

> **Watch out:** deleting a student's account (Flow 1's `DELETE /me`) removes the `analysis` row, summary included, the same `ON DELETE CASCADE` way Flow 4 already describes.

### 4. Loads separately from the charts

`GET /me/analysis` (charts, Best Fit, eligibility) and `GET /me/analysis/summary` (this flow) are 2 separate API calls. The client (`components/AISummaryCard.jsx`, Flow 5 step 6) fires both at once when My Results loads, instead of waiting for the charts to finish first. So a slow GPT-5 reply (up to the 6-second timeout, plus a little overhead) never delays the charts appearing, and a failed summary never breaks the charts -- this is PRD T7 acceptance criterion 7 ("separately, so charts never wait for it") and criterion 5 ("if the AI fails, the charts and Best Fit still show"), both directly.

## Error States

| Error | Cause | Handling |
|---|---|---|
| `401` Wrong email or password | Bad login | One generic message. Doesn't reveal which part was wrong |
| `401` Invalid or expired token | Token expired, tampered, wrong type, or the user was deleted | The client should try `/auth/refresh` once, then send the student to log in |
| `409` Email already registered | Sign-up with a used email | The client asks the student to log in instead |
| `422` Validation error | Bad sign-up data | The client shows the field error |
| `429` Too many requests | More than 5 login or sign-up tries per minute from one IP address | The client asks the student to wait a minute |
| `404` Program not found | `GET /programs/{code}` with a code not in the current session | The client shows a "not found" message |
| `400` Bad SPM result save | `PUT /me/results` with a bad grade, a duplicate subject, a missing `BM`/`SJ` row, or an unknown subject code | The client shows the field error and doesn't save |
| `400` Bad interest-answer save | `PUT /me/interest-answers` with a duplicate question id, an unknown question/option id, an option that doesn't match its question, or a question outside the student's current set | The client shows the error and doesn't save |
| `500` Analysis can't be computed | `GET /me/analysis` when the current session has no `general_requirements` row for the student's category -- a reference-data gap, not something the student did wrong | Not caught as a friendly error yet: it surfaces as a generic server error. The client should show a generic "something went wrong, try again later" message. A developer should treat this as a sign the session's data load is incomplete |
| `200` with `status: "unavailable"` | `GET /me/analysis/summary` when GPT-5 times out (6 seconds), errors, or `OPENAI_API_KEY` is missing/placeholder | Never a `500` (Flow 6 step 1). The client shows "Summary unavailable right now." The charts from `GET /me/analysis` are unaffected either way |

## Defaults

| Setting | Default |
|---|---|
| Access token lifetime | 15 minutes (`JWT_ACCESS_MINUTES`) |
| Refresh token lifetime | 7 days (`JWT_REFRESH_DAYS`) |
| Token signing | HS256 with `JWT_SECRET` |
| Login and sign-up rate limit | 5 per minute per IP address |
| Minimum password length | 8 characters |
| Allowed `spm_year` | 1970 to the current year |
| Allowed websites (CORS) | only `FRONTEND_ORIGIN` |
| Importer pause between requests | 1 second (`REQUEST_DELAY_SECONDS`) |
| Importer retries on a failed request | up to 4, waiting longer each time |
| AI summary request timeout | 6 seconds (`REQUEST_TIMEOUT_SECONDS`, decision `0012`) |
| AI summary request retries | 0 -- never retried automatically (decision `0012`) |
| AI summary word limit | 120 words, enforced in code (`MAX_SUMMARY_WORDS`, decision `0013`) |

## Behavioral Constraints

- Every `/me` route acts only on the account in the access token.
- Passwords, tokens, race and request bodies are never written to logs.
- Refresh and logout have no rate limit yet (only login and sign-up do).
- The reference-data routes (`/subjects`, `/universities`, `/programs`, `/programs/{code}`) need no login and read only the most recently loaded session.
- The importer only fetches one page at a time -- it never runs requests to e-Panduan in parallel.
- `PUT /me/results` is **upsert-only**: it never deletes a subject the payload leaves out. To remove a saved subject, a future route would need to add that on purpose.
- `PUT /me/interest-answers` is a **merge/upsert** (decision `0008`): each save updates only the questions it mentions, leaving every other previously-saved answer untouched. Only questions in the student's current set are accepted.
- `GET /me/analysis`'s interest-area chart, Likely to love, and any interest-driven sweet spot are only ever computed from the student's latest fully answered (40/40) set (decision `0008`, rotation PRD T1); with no finished set they're forced to 0/empty regardless of how many (or which) questions have been answered so far.
- A student has at most one unfinished set at a time. A new set never repeats a question the student has been given until fewer than 40 unseen questions are left (rotation PRD T3).
- Answers are kept only for the current set and the latest finished set. Rotating deletes the unfinished set's answers; finishing a set deletes older sets' answers.
- `PUT /me/results` and `PUT /me/interest-answers` both delete the student's cached `analysis` row on every successful save, unconditionally -- there's no check for whether the save actually changed anything (decision `0006`).
- `GET /me/analysis` only ever computes for, caches, and returns the logged-in student's own data -- the same access-token scoping as every other `/me` route.
- `GET /me/analysis/summary` sends GPT-5 only interest-area and subject-group names + scores -- never email, race, citizenship, raw grades, or a user id (decision `0010`). It never returns a `500`: any AI failure becomes `status: "unavailable"` instead.
- `GET /me/analysis/summary` shares `GET /me/analysis`'s cached `analysis` row and its invalidation rule (decision `0006`, decision `0011`) -- there's no separate cache or separate invalidation path for the summary.
- The AI summary is never computed until the student has a fully (40/40) answered interest test set and at least one SPM result is saved -- the same "enough data" bar `GET /me/analysis`'s charts already use.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals these flows fulfil (T1, T2, T3, T4, T5, T6, T7) |
| `docs/plan/furtherxpert-plan.md` | Plan | How the flows were planned |
| `docs/prd/ui-redesign-prd.md`, `docs/plan/ui-redesign-plan.md` | Intent, Plan | Phase 8: the new look of the Flow 5 pages |
| `docs/reference/folder-structure.md` | Reference | Where each file of these flows lives |
| `docs/decisions/NNNN-*.md` | Decision log | Deviations from the plan |
