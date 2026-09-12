# FurtherXpert Workflow

> **Quick summary**
> - **What:** how the app behaves **today**: what happens, step by step, when a student uses it.
> - **Why:** when you change code, this doc is the spec for current behaviour. If code and this doc disagree, fix one of them.
> - **Now covers:** accounts (sign up, log in, refresh, log out, view and delete account), reference data (the yearly import, plus the subject/university/program lookup routes), student input (saving SPM results, taking or retaking the interest test, reading your own data back), and analysis (Phase 5: the 2 charts, Best Fit, and eligibility, cached and recomputed only when the student's data changes). Each new phase adds its flow here.

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

Describes the live flows of FurtherXpert. So far, that's the **accounts flow** (Phase 2), **reference data** (Phase 3), **student input** (Phase 4), and **analysis** (Phase 5). Only the backend exists yet. There are no screens until Phase 6, so flows start from API requests -- except the yearly import below, which a developer runs by hand.

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

Student input is the SPM (**Sijil Pelajaran Malaysia**, Malaysia's high-school leaving exam) results a student enters by hand, and their answers to the 20-question interest test. Both are personal data, so every route in this flow needs a login, and each route only ever touches the logged-in student's own rows -- the same rule as Flow 1's `/me` routes.

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

**Input:** `GET /interest-test` (no login needed -- it's a fixed question list, not personal data, same as Flow 2's lookup routes). Returns all 20 questions, each with its options' text and id only -- **never** which interest area an option counts toward. That's on purpose: knowing the mapping would let a student game their own score.

**Input:** `PUT /me/interest-answers` with a list of `{question_id, option_id}` pairs.
**Actions:**
1. Check the payload has no repeated question id, and every question id and option id is real.
2. Check each option actually belongs to the question it's paired with -- a mismatched pair (option from a different question) is rejected.
3. **Retake = full replace:** delete every one of the student's previous answers, then insert the new payload's rows, in the same database transaction. So a retake can never leave a mix of old and new answers.
4. A payload doesn't have to cover all 20 questions -- whatever subset is sent becomes the student's whole new answer set. Each interest area's score is worked out from picks made, not from a fixed total (PRD T1), so a partial answer set still scores correctly.

**Output:** `200` with the saved `{question_id, option_id}` pairs.
**On failure:** `400` with a message naming the problem -- a duplicate question id, an unknown question or option id, or an option that doesn't belong to its question.

### 4. Deleting your account cleans up both

`DELETE /me` (Flow 1) removes the student's `spm_results` and `interest_answers` rows automatically, the same way it will for every future student table: the tables point back at `users` with `ON DELETE CASCADE`, so the database removes them as part of deleting the account row -- no extra clean-up code needed.

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
   c. Load the 9 interest areas, and how many of the interest test's questions can award each area a point (its "max picks").
   d. Count the student's own picks per area from their saved interest-test answers ("None of the above" answers don't count toward any area).
   e. Load **syarat am** (general_requirements), the entry rules that apply to every program in this session + category.
   f. Load every program in this session + category, with its own **syarat khas** (program_requirements), and run the eligibility check (Flow 4 step 2's rules) for each one against the student's grades, citizenship, and race.
   g. Compute **Chart 1** (subject-group scores: the mean grade-percent of the subjects the student took in that group; a group with none of its subjects taken is left out entirely, never shown as 0), and **Chart 2** (interest-area scores: picks / max picks, as a percent; every one of the 9 areas is always shown, even at 0%).
   h. Compute **Likely to excel** (top 3 areas by Chart 1's related subject groups; an area is left out if the student has none of its subject groups) and **Likely to love** (top 3 areas by Chart 2's score, **excluding any area that scores 0 interest** -- see decision `0007`). Ties are broken by the other list's score, then by area name. Because 0-score areas are excluded, Likely to love can return 0 to 3 areas -- fewer than 3, or empty if the student hasn't taken the interest test (or picked "None of the above" every time).
   i. **Sweet spot:** any area that appears in both top-3 lists. Since Likely to love can no longer contain a 0-score area, a 0-score area can no longer be a Sweet spot either -- a direct consequence of step h's rule, not a separate check.
   j. **Best Fit:** for every area that appears in *either* top-3 list (the union, not excel-only), show up to 3 of that area's programs -- Eligible ones first, then by name, and only Eligible or Conditional programs, never Not Eligible.
   k. Save the whole result as one row in `analysis` (replacing nothing, since there's no existing row at this point), and return it.

**Output:** `200` with subject-group scores, interest-area scores, Likely to excel, Likely to love, Sweet spot, Best Fit, the category (A/B) used, and `computed_at` (when it was worked out).
**On failure:** if the current session has no `general_requirements` row for the student's category (a data problem, not a student mistake -- see the Error States table below), the request fails with a `500` server error rather than a normal eligibility result.

> **Watch out:** a non-citizen student still gets both full charts (PRD T2: "the charts are still shown") -- only Best Fit's program lists come back empty for them, since a non-citizen can never be Eligible or Conditional for any program (a hard stop, checked first). The same "still show charts" rule applies to a Bumiputera-only program mismatch: it only empties that one program out of Best Fit, not the whole response.

> **Watch out:** the eligibility verdict order is fixed. 1) not a citizen -> Not Eligible. 2) the program is Bumiputera-only and the student isn't -> Not Eligible. 3) the combined syarat am + syarat khas grade rules aren't met -> Not Eligible, with plain-English reasons (for example "Needs C in Matematik — you have D"). 4) an interview/test is needed, or a rule can't be checked automatically (medical, colour-blindness, age) -> Conditional, with reasons. 5) otherwise -> Eligible. Each of the student's subjects can satisfy at most one rule clause across syarat am and syarat khas combined -- see decision `0005` for how that's checked.

### 2. The cache, and when it goes stale

**How it works:** `analysis` holds at most one row per student. The first `GET /me/analysis` after a change computes fresh and saves it; every `GET` after that, until something changes, is served straight from that saved row -- same `computed_at` each time, no recompute.

**Cache invalidation:** both `PUT /me/results` (Flow 3) and `PUT /me/interest-answers` (Flow 3) delete the student's cached `analysis` row as part of their own save, every time they succeed -- there's no check for whether the save actually changed anything. So the very next `GET /me/analysis` after either save always recomputes fresh; it can never return numbers from before that save. See decision `0006` for why this is unconditional rather than diffed.

> **Watch out:** deleting a student's account (Flow 1's `DELETE /me`) removes their `analysis` row too, the same `ON DELETE CASCADE` way as `spm_results` and `interest_answers`.

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
| `400` Bad interest-answer save | `PUT /me/interest-answers` with a duplicate question id, an unknown question/option id, or an option that doesn't match its question | The client shows the field error and doesn't save |
| `500` Analysis can't be computed | `GET /me/analysis` when the current session has no `general_requirements` row for the student's category -- a reference-data gap, not something the student did wrong | Not caught as a friendly error yet: it surfaces as a generic server error. The client should show a generic "something went wrong, try again later" message. A developer should treat this as a sign the session's data load is incomplete |

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

## Behavioral Constraints

- Every `/me` route acts only on the account in the access token.
- Passwords, tokens, race and request bodies are never written to logs.
- Refresh and logout have no rate limit yet (only login and sign-up do).
- The reference-data routes (`/subjects`, `/universities`, `/programs`, `/programs/{code}`) need no login and read only the most recently loaded session.
- The importer only fetches one page at a time -- it never runs requests to e-Panduan in parallel.
- `PUT /me/results` is **upsert-only**: it never deletes a subject the payload leaves out. To remove a saved subject, a future route would need to add that on purpose.
- `PUT /me/interest-answers` is a **full replace** every time: it always clears the student's previous answers first, then saves the new payload as the whole new set.
- `PUT /me/results` and `PUT /me/interest-answers` both delete the student's cached `analysis` row on every successful save, unconditionally -- there's no check for whether the save actually changed anything (decision `0006`).
- `GET /me/analysis` only ever computes for, caches, and returns the logged-in student's own data -- the same access-token scoping as every other `/me` route.

## Related Documents

| Document | Type | Relationship |
|---|---|---|
| `docs/prd/furtherxpert-prd.md` | Intent | Product goals these flows fulfil (T1, T2, T3, T4, T5, T6) |
| `docs/plan/furtherxpert-plan.md` | Plan | How the flows were planned |
| `docs/reference/folder-structure.md` | Reference | Where each file of these flows lives |
| `docs/decisions/NNNN-*.md` | Decision log | Deviations from the plan |
