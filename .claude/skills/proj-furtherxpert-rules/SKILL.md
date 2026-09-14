---
name: proj-furtherxpert-rules
description: FurtherXpert domain rulebook — SPM grade points, subject groups, interest-area scoring, Best Fit, UPU syarat am/khas eligibility (categories A/B, counts-once, Bumiputera, Conditional), reference-data import via Alembic, and the golden sample students. Use before building or reviewing anything that touches scoring, eligibility, reference data, or the interest test.
---

# FurtherXpert rules

Source of truth: `docs/prd/furtherxpert-prd.md` T1, T2, T5. This skill is the working
checklist; if it disagrees with the PRD, the PRD wins. Report the mismatch.

## 1. Where the rules live

- `backend/app/services/scoring.py`: grade points, subject groups, interest areas, Best Fit.
- `backend/app/services/eligibility.py`: UPU checker.
- Both are **pure functions**: plain data in, plain data out.
  - No DB session, no HTTP, no clock, no randomness.
  - Routers load the data and call them.
- The client **only displays** results. Never duplicate a formula in React.

## 2. Scoring

| Rule | Value |
|---|---|
| Grade points | A+ 9, A 8, A- 7, B+ 6, B 5, C+ 4, C 3, D 2, E 1, G 0 |
| Percent | points ÷ 9 × 100, rounded to 1 decimal **only at the API edge** |
| Strong / weak | ≥ 7 (A-) / ≤ 3 (C) |
| Subject group score | mean percent of subjects taken in the group; groups with none taken are **omitted** |
| Interest area score | picks ÷ max possible picks for that area **in the student's latest finished 40-question set** × 100; "None of the above" = 0 picks. No finished set → all 9 areas 0, love list empty (rotation PRD T1) |
| Excel score (area) | mean of the area's subject-group scores the student has; omit the area if none |
| Top lists | excel: top 3 by excel score (unchanged). love: top 3 by interest score, **excluding any area scoring 0** — so love holds 0-3 areas, never padded with 0-score filler. Same tie-break (other score desc, then area name asc) for whichever entries remain in each list |
| Sweet spot | area present in both top-3 lists |
| Programs per area | Eligible first, then Conditional, then name; max 3; never Not Eligible |

- Unknown grades (B-, C-, F, blanks) are **validation errors at input**. Never score them as 0.
- Every interest tag maps to exactly one area. A test must assert there are no duplicates.
- Area ↔ NEC prefix ↔ subject-group mapping lives in the `interest_areas` table (seeded by migration). See PRD T1.

## 3. UPU eligibility

**Category:** SPM year equals the session's `latest_spm_year` → A. Otherwise → B.

**Rule tree** (`general_requirements.rules` / `program_requirements.rules`, JSONB):

| Node | Meaning |
|---|---|
| `{"subject": S, "min": G}` | subject S at grade G or better |
| `{"one_of": [S…], "min": G, "count": n}` | n (default 1) of the listed subjects at G or better |
| `{"uncounted": n, "min": G}` | n subjects not used by any other clause, at G or better |
| `{"any": [node…]}` | at least one branch passes (UPU "ATAU") |
| `{"all": [node…]}` | every branch passes |

Top-level flags: `bumiputera_only`, `interview`, and `unverifiable` (a list of Malay notes the grades can't check).

**Algorithm rules:**
1. Syarat am and syarat khas are evaluated **together** as one `all`. Each student subject is used **at most once** across every clause.
2. Use backtracking or bipartite matching. Never use a greedy first-fit.
   - Example trap: Math C could satisfy both "C in Matematik" and an `uncounted` slot. Greedy can wrongly fail or pass.
   - Subject counts are small (≤ 15), so backtracking is fine.
3. Order of verdicts:
   - Not a citizen → Not Eligible.
   - `bumiputera_only` and not Bumiputera → Not Eligible.
   - Grade tree fails → Not Eligible.
   - `interview` or a non-empty `unverifiable` → Conditional.
   - Otherwise → Eligible.
4. Bumiputera = race in {Melayu, Anak Negeri Sabah, Anak Negeri Sarawak, Orang Asli}.
5. Return reasons as short English strings, e.g. `"Needs C in Matematik — you have D"` or `"Requires interview/test"`. Keep the original Malay rule text for the detail page.
6. Subject identity: e-Panduan uses Malay names, including "/" alternatives and old-syllabus names.
   - Map them through the `subjects` table codes.
   - An unmapped subject name in the snapshot is an **import error**, not a silent skip.

## 4. Reference data

1. `backend/app/importer/epanduan.py` fetches e-Panduan sequentially and writes `backend/data/upu/<session>.json`.
   - Programs come from `ProgramPengajian/kategoriCalon/{A|B}?page=N`.
   - Rules come from `ProgramPengajian/modalSyarat/{A|B}/{code}`, sent with header `X-Requested-With: XMLHttpRequest`.
   - UA diploma codes match `^U[A-Z]4`.
2. The importer **parses the Malay rule text into the rule tree**. Parsing failures are listed in the snapshot's `unparsed` array.
   - Never guess: those programs become Conditional with the raw text shown.
3. A new Alembic data migration loads the snapshot. It **replaces** all reference rows for the session.
4. Snapshot facts (sesi 2026/2027):
   - Category A: 166 UA diplomas across 11 universities.
   - Category B: 162 UA diplomas.
   - 81 are Bumiputera-only; 32 require an interview.
   - Syarat am, same for A and B: MyKad citizen; C in BM, E in Sejarah, plus 2 more C in uncounted subjects.

## 5. Golden sample students

Fixtures: `backend/tests/golden/students.json`. Expected outputs: `backend/tests/golden/expected/*.json`.

| Name | Profile | What it exercises |
|---|---|---|
| Amir | Melayu, citizen, SPM latest year; strong Math/Sciences; tech-heavy interests | Eligible for `UE4481001`; Science & Tech sweet spot |
| Mei Ling | Cina, citizen; same grades as Amir | Not Eligible for `UE4481001` (Bumiputera-only) but Eligible for a non-UiTM equivalent |
| Priya | India, citizen, older SPM (category B); arts + media interests; took an old-syllabus subject | Category B rule set; Arts group visible |
| Rahman | Anak Negeri Sabah, citizen; borderline grades (C/D) | Counts-once trap; Conditional via interview program |
| Aisyah | Melayu, citizen; no science subjects | Sciences group hidden; Healthcare excluded from "excel" |
| Daniel | Non-citizen; good grades | Not Eligible everywhere; charts still computed |

**Rules for golden tests:**
- Expected values change **only** for an intended rule change.
- The change note must say which rule changed and why.

## 6. Review checklist

- [ ] No formula lives in the client or in a router.
- [ ] No unknown grade reaches scoring.
- [ ] Interest tags are unique per area; normalised by max picks within the student's own set, not the whole 300-question bank.
- [ ] "Why this diploma?" (Phase 10) uses `eligibility.find_matching` (the checker's own backtracking, each subject once) and the charts' 1-decimal rounding; built by code, never AI; never shows race or interest test questions/answers.
- [ ] Counts-once holds (a test covers the trap).
- [ ] Category A/B chosen from SPM year vs `latest_spm_year`.
- [ ] Bumiputera and citizenship hard stops come before grade checks.
- [ ] Reference data changed only via snapshot + migration.
- [ ] Golden tests pass; any expected-value change is justified.
