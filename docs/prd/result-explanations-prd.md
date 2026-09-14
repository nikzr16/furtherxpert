# Why This Diploma?

> **What kind of doc is this?** A product brief, also called a **PRD** (Product Requirements Document). It says **what** we're building and **why**. It does not say how.
>
> **Keep it updated?** No. If plans change while building, don't edit this doc. Add a note to the decision log (`docs/decisions/`) instead.

<!-- AI Context
Role: This doc captures what the per-diploma explanation feature should do and why.
For how to build it, read `docs/plan/result-explanations-plan.md`.
It adds to `docs/prd/furtherxpert-prd.md` T1 (Best Fit), T2 (eligibility) and T6
(the `GET /me/analysis` response). It changes no score, rank, program order or
eligibility verdict: it only explains the ones that already exist.
Reader: a layman. Follow `docs/layman-guide.md`.
Do not rewrite this doc during coding. If the build drifts from what's written
here, add a decision log entry instead.
-->

## Quick summary

- **What:** every diploma suggested on My Results gets a **"Why this diploma?"** section explaining why it is suggested to this student.
- **Why:** today a diploma just shows a name, a university and "Eligible". The student can't see how it links to their strengths or interests, or which of their grades got them in.
- **For who:** students reading their Best Fit, and the parents or counsellors helping them.
- **Done when:** every suggested diploma says, with the student's own grades and scores, why it's there.
- **Status:** Draft (2026-09-14, rewritten after product owner feedback). Waiting for approval.

---

## 1. What problem are we solving?

Best Fit lists up to 3 diplomas under each area. Each shows only its name, university and a verdict. A student can't tell:
- why this diploma belongs to this area,
- why that area was picked for them,
- which of their grades meet its entry rules,
- or why these 3 are shown and not others.

> **Example:** Under "Business & Management — Likely to excel", Amir sees "Diploma Analisis Pelaburan — Eligible". Nothing says it's a finance diploma, that his Mathematics and Commerce grades put this area in his top 3, or that his BM, Sejarah and 2 other grades meet the entry rules.

## 2. Who is this for?

Also called: **user stories**.

1. **A student** wants to **see why a diploma fits their strengths or interests** so they can **trust the suggestion**.
2. **A student** wants to **see which of their grades meet each entry rule** so they can **apply with confidence, or spot a grade they typed wrong**.
3. **A student** wants to **know what's still needed for a Conditional diploma** so they can **prepare for it**, for example an interview.
4. **A student** wants to **know why these diplomas are shown and not others** so they can **go and browse the rest**.
5. **A counsellor or parent** wants to **follow the reasoning** so they can **talk it through with the student**.

## 3. What we're building

Also called: **scope**.

A **"Why this diploma?"** section under every diploma in Best Fit. It can be opened and closed, and starts closed. It has 4 parts.

**1. Why it matches you** (the area link)
- Which field of study the diploma teaches, and which interest area that belongs to.
- Why that area was suggested: its place in Likely to excel, Likely to love, or both (Sweet spot), with the score and what the score came from.
- > **Example:** "This is a finance diploma: its field of study, Kewangan, Perbankan Dan Insurans (code 0412), is part of Business & Management. Business & Management is #2 in what you're likely to excel in, at 83.3%, from your Mathematics (88.9%) and Commerce (77.8%) grades."
- > **Example (love):** "Science & Technology is #1 in what you're likely to love, at 50%: you picked a Science & Technology answer in 9 of the 18 questions that offered one."
- > **Example (sweet spot):** "It's a Sweet spot: this area is in your top 3 for both what you're likely to excel in and what you're likely to love."

**2. How you meet the entry rules** (for UPU group A or B)
- Every rule, with the grade of yours that meets it. Each of your subjects is used only once, the same way the checker counts it.
- General UPU rules (**syarat am**) and this diploma's own rules (**syarat khas**) are shown separately.
- > **Example:**
  > - General rules: Bahasa Melayu — needs C, you have A+. Sejarah — needs E, you have A. 2 more subjects at C or better — Bahasa Inggeris (A), Kimia (A).
  > - This diploma's rules: Matematik — needs C, you have A+. One of Fizik / Kimia / Biologi at C — Fizik (A+).
  > - Or: "No extra subject rules beyond the general ones."
- For a **Bumiputera-only** diploma: "Only open to Bumiputera students — you qualify."

**3. Anything still needed**
- **Eligible:** "Nothing else needed — no interview or test."
- **Conditional:** what's left, using the existing reasons. For example: "You'll need to pass an interview or test."

**4. Why it's in this top 3**
- > **Example:** "1 of 9 diplomas you can apply for in Business & Management. Eligible ones are shown first, then A to Z. See all of them on Explore."

## 4. What we're NOT building (on purpose)

Also called: **non-goals** or **out of scope**.

- **AI-written explanations**, because the words must match the grades and numbers exactly (main PRD section 6).
- **Changing how diplomas are picked or ordered**, because this feature only explains today's rules (Eligible first, then A to Z). Ranking by "best fit" can be a later phase.
- **Explanations for Not Eligible diplomas**, because Best Fit never shows them. Their existing reasons already say what's missing.
- **Explanations on Explore or Program Detail**, because those aren't personal suggestions.
- **Showing which interest test answers were picked**, because it would reveal which answer counts toward which area (main PRD T6). Counts only.
- **An area-level "Why this?" on each card**, because the product owner wants the explanation on each diploma.

> **Why this matters:** writing this down stops the project from quietly growing bigger than planned.

## 5. How we'll know it's done

Also called: **acceptance criteria**.

| # | It's done when... | How we check |
|---|---|---|
| 1 | Every diploma in Best Fit has all 4 parts | Automated test |
| 2 | The area link names the diploma's field of study and code, and the area's rank, score and source (grades or answers) | Golden tests with hand-worked numbers |
| 3 | Every entry rule is listed with the student's grade that meets it, and no subject is used twice | Unit tests + golden tests, checked by hand against e-Panduan rules |
| 4 | The grades listed for a diploma are the same on every visit | Automated test run repeatedly with shuffled inputs |
| 5 | A diploma with no extra rules says so | Automated test (for example `UE4343004`) |
| 6 | A Conditional diploma says what's still needed; an Eligible one says nothing else is needed | Automated test |
| 7 | The "1 of N" count and order match the diplomas actually shown | Automated test |
| 8 | Scores, Best Fit, program order and verdicts are exactly the same as before | Existing golden tests pass with numbers unchanged |
| 9 | Explanations never name an interest test question or answer, and never go to the AI | Automated test |
| 10 | "Why this diploma?" opens and closes by mouse, keyboard and screen reader, at phone and laptop width | Try it by hand in a browser |

## 6. Rules and limits

Also called: **constraints**.

- **Code only, never AI.** Built from the same data as the charts and the checker (main PRD section 6).
- **Must agree with the checker.** An explanation can't show a way of meeting the rules that the checker wouldn't accept. Each subject counts once (main PRD T2).
- **Numbers match the screen.** Same 1-decimal rounding as the charts.
- **Don't reveal answer-to-area links** (main PRD T6).
- **Privacy (PDPA 2010).** No new data is collected. Race isn't shown: a Bumiputera-only diploma only says "you qualify". Explanations are never logged, and never sent to GPT-5 (main PRD T4).
- **Plain words.** Follow `docs/layman-guide.md`, and explain codes.

## 7. Decisions already made

| Decision | Why we chose it |
|---|---|
| Explain each diploma, not each area card | The product owner asked for it (2026-09-14, with a screenshot of Best Fit) |
| Show the grade that meets each rule | It's the most useful "why", and it helps catch typing mistakes |
| The backend writes the sentences | They can be tested with the golden students. The page only displays them, like eligibility reasons today |
| Say honestly that the top 3 are "Eligible first, then A to Z" | That is the real rule. Pretending it's a fit ranking would mislead |
| Subject names shown as on the SPM certificate (Malay), for example "Matematik" | Students recognise them, and they match the Malay rule text on Program Detail |
| "Why this diploma?" starts closed | Keeps the list short. Students open it when they want to know |

## 8. Questions we still need to answer

- [ ] Should Best Fit later rank diplomas by how well they fit (for example average merit, or rules matching the student's strongest subjects), instead of A to Z?

---

## Words to know

| Word | What it means here |
|---|---|
| Best Fit | The diplomas shown on My Results under each suggested area, up to 3 per area |
| Likely to excel | Top 3 areas by the student's grades in the subject groups tied to each area |
| Likely to love | Top 3 areas by interest test score |
| Sweet spot | An area in both top-3 lists |
| Field of study code | Malaysia's NEC code for what a course teaches. For example, 0412 = finance, banking and insurance |
| Syarat am | UPU's general entry rules, the same for every diploma |
| Syarat khas | A diploma's own extra entry rules |
| UPU group A / B | A = this year's SPM leavers, B = older SPM holders. Rules can differ |
| Eligible / Conditional | Meets every rule / meets the grade rules but still needs something like an interview |
| Golden test | A test with fixed sample students and hand-worked expected answers |

## Where this fits

**Roadmap phase:** Phase 10, Why this diploma (to be added to `docs/product-roadmap.md` once this PRD is agreed).

| Related doc | What it tells you |
|---|---|
| `docs/product-roadmap.md` | When this gets built, compared to other work |
| `docs/plan/result-explanations-plan.md` | How we'll build it |
| `docs/prd/furtherxpert-prd.md` | The Best Fit, eligibility and area rules being explained (T1, T2, T6) |
| `docs/prd/interest-test-rotation-prd.md` | Why love scores count questions within the student's own set |
| `docs/furtherxpert-workflow.md` | How it works once it's built (Flow 4, My Results page) |
| `docs/decisions/0005-*.md` | How the checker makes each subject count once |

---

## Technical details (for the person building this)

### T1. What each part is built from

| Part | Built from |
|---|---|
| Area link | the program's `nec_code` + `nec_name`; the matched area (main PRD T1 prefix table); that area's place in `likely_to_excel` / `likely_to_love`; excel subject groups with scores, or love picks / offered counts |
| Entry rules | the same combined rule tree the checker uses (syarat am first, then syarat khas), with one valid way of meeting it: which subject met which rule |
| Bumiputera line | the combined `bumiputera_only` flag only. Race is never shown |
| Still needed | the verdict and its existing `reasons` |
| Top-3 line | the program's position in the shown list, and the count of Eligible + Conditional programs in the area |

### T2. Response addition (`GET /me/analysis`)

Each program inside `best_fit[].programs[]` gains a `why` object:

```json
{
  "match": ["This is a finance diploma: its field of study, ...", "Business & Management is #2 in ..."],
  "rules": [
    {"title": "General UPU rules (syarat am)", "lines": ["Bahasa Melayu — needs C, you have A+"]},
    {"title": "This diploma's rules (syarat khas)", "lines": ["No extra subject rules beyond the general ones."]}
  ],
  "still_needed": ["Nothing else needed — no interview or test."],
  "position": "1 of 9 diplomas you can apply for in Business & Management. ..."
}
```
