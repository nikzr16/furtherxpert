# FurtherXpert

> **What kind of doc is this?** A product brief, also called a **PRD** (Product Requirements Document). It says **what** we're building and **why**. The technical details section at the end gives the exact rules the builder needs.
>
> **Keep it updated?** No. If plans change while building, don't edit this doc. Add a note to the decision log (`docs/decisions/`) instead.

<!-- AI Context
Role: This doc captures what FurtherXpert should do and why. It is the
single source of truth for product behaviour. The "Technical details" section
(T1–T8) holds the exact rules; skills and code comments cite those section ids.
Reader: a layman. Follow `docs/layman-guide.md`.
Do not rewrite this doc during coding. If the build drifts from what's written
here, add a decision log entry instead.
FurtherXpert is a full revamp. The older SambungBelajarmu docs and code in `sambungbelajarai/` and
`archieve-sambung/` do not define behaviour.
-->

## Quick summary

- **What:** a website where Malaysian SPM holders see what they're **best at**, what they **enjoy most**, and which public-university diplomas they qualify for.
- **Why:** SPM leavers often don't know which course suits them, or whether they can get in. The official rules are long and scattered.
- **For who:** students who have finished SPM (usually about 17–18 years old).
- **Done when:** a student can sign up, enter results, take the interest test, and see 2 charts plus programs they really qualify for, all checked against official rules.
- **Status:** Agreed (2026-09-12). Building.

---

## 1. What problem are we solving?

After SPM, students must pick a diploma course with little help. They don't know which subjects they're strong in, or which fields suit their interests. Checking the official entry rules for each course takes hours.

> **Example:** Amir (17, Johor) got good Maths and Science grades. He likes tech but also enjoys design. He doesn't know if UiTM's computing diploma would accept him.

## 2. Who is this for?

Also called: **user stories**.

1. **An SPM leaver** wants to **see their strong and weak subject areas** so they can **pick a course they'll do well in**.
2. **An SPM leaver** wants to **see which fields they're most interested in** so they can **pick a course they'll enjoy**.
3. **An SPM leaver** wants to **know which UA diplomas they qualify for, and why** so they can **apply with confidence**.
4. **An older SPM holder** (not this year's batch) wants **the same answers using the rules for their group** so the results are **accurate for them**.

## 3. What we're building

Also called: **scope**.

- **Accounts:** sign up, log in, log out, delete account.
- **SPM results form:** subjects and grades, including older-syllabus subjects.
- **Interest test:** 20 questions with 5 options each. It can be retaken.
- **Chart 1, subject strengths:** a **spider chart** (a web-shaped chart, also called a radar chart) of subject groups.
- **Chart 2, interests:** a spider chart of 9 interest areas.
- **Best Fit:** the top 3 areas the student will **likely excel in**, and the top 3 they'll **likely love**. An area in both lists is a **Sweet spot**. Each area shows up to 3 matching programs.
- **Eligibility check:** every program shows **Eligible**, **Conditional** or **Not Eligible**, with reasons.
- **AI summary:** a short plain-words explanation of the charts, written by GPT-5.
- **Explore:** browse and filter all UA diploma programs.

Only **diploma programs at public universities** (UA, Universiti Awam) are included. Both UPU candidate groups are covered: this year's SPM leavers and older SPM holders.

## 4. What we're NOT building (on purpose)

Also called: **non-goals** or **out of scope**.

- **Private universities** (IPTS), because the first version focuses on the official public-university system.
- **Asasi, Matrikulasi, polytechnics, Kolej Komuniti, degrees**, because diplomas come first. Other routes can follow later.
- **Financial aid, maps, chat**, because FurtherXpert focuses on "what suits me" and "can I get in".
- **Malay-language screens**, because English is simpler to start with. Official rule text is still shown in its original Malay.
- **Calculating the student's own merit score**, because UPU's merit formula is a separate project. We only show each program's average merit.
- **Admin screens**, because the data comes from official imports for now. The database is ready for them later.
- **Teacher or parent dashboards**, because students are the only users for now.

> **Why this matters:** writing this down stops the project from quietly growing bigger than planned.

## 5. How we'll know it's done

Also called: **acceptance criteria**.

| # | It's done when... | How we check |
|---|---|---|
| 1 | 6 sample students get the exact expected chart and Best Fit numbers | Automated test (**golden tests**, T1) |
| 2 | Eligibility matches the official e-Panduan site for the test programs | Automated test with real programs (T2) |
| 3 | One SPM subject can never count for 2 rules at once | Automated test (T2) |
| 4 | A wrong password is rejected, an expired login is rejected, and student A can't see student B's data | Automated test (T3) |
| 5 | If the AI fails, the charts and Best Fit still show | Automated test (T4) |
| 6 | Charts and Best Fit load in under 2 seconds | Measure it |
| 7 | The AI summary loads in under 10 seconds, separately, so charts never wait for it | Measure it |
| 8 | A student finishes the whole flow in under 10 minutes | Try it by hand |
| 9 | Students rate the results page 4/5 or higher for clarity | User survey |
| 10 | A counsellor agrees with Best Fit for at least 75% of sample students | Counsellor review |
| 11 | `docker compose up --build` starts everything with the data loaded | Try it by hand |

## 6. Rules and limits

Also called: **constraints**.

- **Official rules only.** Eligibility follows UPU's syarat am and syarat khas, taken from the e-Panduan website (T2, T5).
- **Charts come from code, never from AI.** The same answers must always give the same chart.
- **Privacy law.** Follow Malaysia's **PDPA** (Personal Data Protection Act 2010). Collect only what's needed (T4).
- **Race is asked, carefully.** Some programs are for Bumiputera students only. So sign-up asks for race, and uses it **only** for that check.
- **Tools we must use:** FastAPI, React, Tailwind CSS, Recharts, PostgreSQL, Docker, uv, Alembic, and OpenAI GPT-5 (T8).
- **Don't touch** the old SambungBelajarmu folders `sambungbelajarai/` and `archieve-sambung/`.

## 7. Decisions already made

| Decision | Why we chose it |
|---|---|
| Full revamp: the old SambungBelajarmu aim doesn't apply | The product goal changed to "strengths + interests + eligibility" |
| UA diplomas only | Keeps the first release focused. Other routes can follow later |
| Cover UPU groups A and B | Older SPM holders apply too, and their rules can differ |
| Follow UPU rules exactly | Students need answers they can trust |
| Ask race at sign-up | 81 of 166 UA diplomas are Bumiputera-only. Guessing would mislead students |
| Ask Malaysian citizenship at sign-up | UPU only accepts Malaysian citizens |
| Subject chart uses groups, not single subjects | Students take different subjects. Groups make charts comparable |
| Best Fit shows both "excel" and "love" lists | Students should see strength and interest separately |
| Keep the Explore page | Students want to browse beyond their Best Fit |
| Real login with stateless JWT | Students return to their saved results |
| PostgreSQL holds all data, including programs | An admin can edit data later |
| Starter data loads through Alembic migrations | One repeatable way to set up every database |
| The yearly UPU import replaces the old year, including admin fixes | New official data is the truth. Nothing goes stale |
| GPT-5 writes the summary only | Keeps the numbers reliable and testable |
| React + Tailwind CSS + Recharts | Team choice. Recharts has a ready-made spider chart |
| uv for Python | Fast and repeatable Python setup |

## 8. Questions we still need to answer

- [ ] Is the subject-group and interest-area mapping right? A school counsellor should review T1.
- [ ] Which counsellor reviews the sample students for acceptance check 10?

---

## Words to know

| Word | What it means here |
|---|---|
| SPM | Sijil Pelajaran Malaysia, the exam students take at about 17 |
| UA | Universiti Awam, a Malaysian public university. There are 20 |
| UPU | Unit Pengambilan Pelajar, the government office that handles entry to public universities |
| e-Panduan | UPU's official website listing every program and its entry rules |
| Syarat am | UPU's general entry rules, the same for every diploma |
| Syarat khas | Extra entry rules set by each program |
| Category A / B | UPU's groups: A = this year's SPM leavers, B = older SPM holders |
| Bumiputera | Under UPU's rules: Melayu, Anak Negeri Sabah, Anak Negeri Sarawak, or Orang Asli |
| NEC code | Malaysia's national code for a field of study. For example, 0613 = Computer Science |
| Merit | UPU's score for ranking applicants. We only show each program's average |
| Spider chart | A web-shaped chart. Each spoke is one thing measured. Also called a radar chart |
| Golden test | A test with fixed sample inputs and fixed expected answers. If a number changes, the test fails |
| JWT | JSON Web Token, a signed login pass the browser sends with each request |
| Stateless | The server keeps no list of who is logged in. It just checks the pass's signature |
| Database | Where the app saves data. We use PostgreSQL |
| Migration | A step-by-step update to the database's layout or starter data. We use Alembic |
| API | The list of requests the website can send to the server |
| PDPA | Personal Data Protection Act 2010, Malaysia's data privacy law |

## Where this fits

**Roadmap phase:** covers Phases 1–7 in `docs/product-roadmap.md`.

| Related doc | What it tells you |
|---|---|
| `docs/product-roadmap.md` | When each part gets built |
| `docs/project-knowledge.md` | Background knowledge about the project's world (starter, not filled in yet) |
| `docs/reference/folder-structure.md` | Where the files live |
| `docs/decisions/NNNN-*.md` | What changed from this doc while building, and why |

---

## Technical details (for the person building this)

These are the exact rules. Section ids (T1–T8) are cited by the project skills and code.

### T1. Scoring (code only, never AI)

**Grade points:** A+ 9 · A 8 · A- 7 · B+ 6 · B 5 · C+ 4 · C 3 · D 2 · E 1 · G 0.
- **Strong** = A- or better (7 or more). **Weak** = C or worse (3 or less).
- Percent = points ÷ 9 × 100.
- SPM has no B-, C- or F grades. Reject them as input errors.

**Subject groups (Chart 1).** A group's score is the average percent of the subjects the student took in it. A group with no subjects taken is **hidden**, not shown as 0. The required subjects always give at least 3 groups.

| Group | Subjects (examples; the full list is in the `subjects` table) |
|---|---|
| Languages | Bahasa Melayu, Bahasa Inggeris, Kesusasteraan |
| Mathematics | Matematik, Matematik Tambahan |
| Sciences | Fizik, Kimia, Biologi, Sains, Sains Tambahan |
| Humanities | Sejarah, Geografi, Pendidikan Islam / Pendidikan Moral |
| Commerce | Ekonomi, Prinsip Perakaunan, Perniagaan |
| Technical & ICT | Sains Komputer, Grafik Komunikasi Teknikal, engineering subjects |
| Arts | Pendidikan Seni Visual, Reka Bentuk Grafik, Produksi Multimedia |

**Interest areas (Chart 2).** An area's score = the student's picks for it ÷ the most picks possible for it × 100.
- Each answer tag belongs to **exactly one** area.
- "None of the above" counts for nothing.

**Area mapping** (first version, for counsellor review):

| Area | Programs by NEC code prefix | Subject groups used for "excel" |
|---|---|---|
| Science & Technology | 05 (except 052), 06, 07 | Mathematics, Sciences, Technical & ICT |
| Business & Management | 041 | Mathematics, Commerce |
| Law & Governance | 042 | Languages, Humanities |
| Healthcare & Social Services | 09 | Sciences |
| Arts & Design | 021 | Arts |
| Education & Humanities | 01, 022, 023 | Languages, Humanities |
| Hospitality & Tourism | 101 | Languages, Commerce |
| Agriculture & Environment | 08, 052 | Sciences |
| Media & Communications | 032 | Languages, Arts |

Programs whose NEC code matches no prefix still appear in Explore, but not in Best Fit.

**Best Fit**
- **Likely to excel:** an area's score is the average of its subject groups the student took. Areas with none of those groups are left out. Top 3.
- **Likely to love:** the area's interest score. Top 3.
- **Ties:** broken by the other score, then by area name.
- **Programs per area:** only Eligible or Conditional ones. Eligible first, then by name. Max 3.

### T2. UPU eligibility

**Source:** e-Panduan UPU (run by KPT, Kementerian Pengajian Tinggi), <https://online.mohe.gov.my/epanduan/>.

**Snapshot, sesi 2026/2027:**
- Category A: 166 UA diplomas across 11 universities.
- Category B: 162 UA diplomas.
- 81 are Bumiputera-only, and 32 need an interview or test.

**Category:** worked out from the student's SPM year. The latest SPM for the loaded session is **A**. For example, SPM 2025 is A for sesi 2026/2027. Any earlier year is **B**. The session data stores its latest SPM year.

**Syarat am** (the same for A and B):
- Malaysian citizen with a MyKad.
- SPM with at least C in Bahasa Melayu, E in Sejarah, and C in 2 more subjects not already counted.

**Syarat khas** is stored **per program and per category**, because B lists older-syllabus subjects. It's saved as a rule tree the code can check, plus the original Malay text:

```json
{
  "all": [
    {"subject": "BI", "min": "C"},
    {"one_of": ["MT", "FIZ", "KIM"], "min": "C"},
    {"any": [ {"subject": "MT", "min": "C"}, {"subject": "MM", "min": "C"} ]},
    {"uncounted": 2, "min": "C"}
  ],
  "bumiputera_only": true,
  "interview": true
}
```

**How the checker decides:**
- **Each subject counts once** across syarat am and syarat khas. Use a search or matching method, not a greedy first-fit.
- Not a Malaysian citizen → **Not Eligible** for every program. The charts are still shown.
- Bumiputera-only program + non-Bumiputera student → **Not Eligible**.
- An interview or test, or any rule grades can't check (medical, colour-blindness, age) → **Conditional**, with the reason shown.
- Every result carries readable reasons. For example: "Needs C in Matematik — you have D".

### T3. Login (stateless JWT)

- **Access token:** lasts 15 minutes. Kept in browser memory and sent as `Authorization: Bearer`.
- **Refresh token:** lasts 7 days. Stored in an `httpOnly` + `Secure` + `SameSite=Strict` cookie.
- Passwords are scrambled with **argon2** (hashed).
- Login is limited to 5 attempts per minute per IP address.
- Logging out clears the cookie. Because the server is stateless, it keeps no revoke list.
- Every `/me/*` query is limited to the logged-in user's id.

### T4. Privacy (PDPA 2010)

- Sign-up explains that race is used **only** to check Bumiputera-only programs.
- Collect only: email, password hash, citizenship, race, SPM year, grades, and test answers.
- GPT-5 receives **scores only**. Never email, race, or raw grades.
- Never log grades, answers, race, tokens, or AI replies.
- Deleting an account removes all of the user's rows.
- CORS (which websites may call the API) allows only `FRONTEND_ORIGIN`.
- If the AI call fails, the summary is empty, and the charts and Best Fit still work.

### T5. Data and the yearly import

**Student tables:** `users`, `spm_results`, `interest_answers`, and `analysis`. The last one caches the scores, Best Fit, AI summary and time computed.

**Reference tables:** `universities`, `programs`, `campuses`, `general_requirements` (per category), `program_requirements` (per program and category), `subjects` (with an old-syllabus flag), `subject_groups`, `interest_areas`, `interest_questions`, and `interest_options`.

**Program fields:** code (for example `UE4481001`), name, university code, NEC code, semesters, study mode, flags (STEM, TVET, Bumiputera-only, interview), average merit, session, campuses, and career paths.

**Yearly import:**
1. An import script reads e-Panduan and writes a snapshot, such as `backend/data/upu/2026-2027.json`.
2. A new Alembic **data migration** loads it. It **replaces** the previous session's reference data, including admin edits.
3. The website credits the source: "Source: e-Panduan UPU, KPT, sesi 2026/2027".

> **Watch out:** the import script breaks if KPT changes its website. The saved snapshot keeps the app working in the meantime.

### T6. API

| Request | Purpose |
|---|---|
| `GET /health` | Is the server up? |
| `POST /auth/register` · `/auth/login` · `/auth/refresh` · `/auth/logout` | Accounts |
| `GET /me` · `DELETE /me` | Current account / delete it |
| `GET /me/results` · `PUT /me/results` | SPM results |
| `GET /interest-test` · `PUT /me/interest-answers` | Interest test |
| `GET /me/analysis` | Both charts + Best Fit + eligibility |
| `GET /me/analysis/summary` | AI summary (a separate call) |
| `GET /subjects` · `GET /universities` | Form and filter lists |
| `GET /programs` · `GET /programs/{code}` | Explore + program detail |

### T7. Pages

- **Pages:** Register, Login, SPM Results, Interest Test, **My Results** (2 charts, Best Fit, AI summary), Explore, Program Detail, Account.
- **Accessibility:** each chart has a text-table version for screen readers. This follows WCAG AA, the web accessibility standard.

### T8. Folders, commands, settings

```
furtherxpert/
├─ backend/            FastAPI · uv · Alembic · pytest
├─ client/             React · Vite · Tailwind CSS v4 · Recharts
└─ docker-compose.yml  backend + client + PostgreSQL
```

```bash
docker compose up --build
```

```bash
docker compose exec backend uv run alembic upgrade head
```

```bash
docker compose exec backend uv run pytest
```

**Settings (`.env`):**
- **Database:** `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
- **Login:** `JWT_SECRET`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`.
- **AI:** `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5`.
- **Website address:** `FRONTEND_ORIGIN`.
