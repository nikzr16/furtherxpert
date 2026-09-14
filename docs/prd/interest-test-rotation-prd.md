# Interest Test Rotation

> **What kind of doc is this?** A product brief, also called a **PRD** (Product Requirements Document). It says **what** we're building and **why**. It does not say how.
>
> **Keep it updated?** No. If plans change while building, don't edit this doc. Add a note to the decision log (`docs/decisions/`) instead.

<!-- AI Context
Role: This doc captures what the interest test rotation feature should do and why.
For how to build it, read `docs/plan/interest-test-rotation-plan.md`.
It changes these rules in `docs/prd/furtherxpert-prd.md`: section 3 "Interest test"
(20 questions → a 40-question set drawn from a 300-question bank) and T1 "Interest
areas" (completeness and the "most picks possible" count now come from the
student's own set). Everything else in that PRD still applies.
Reader: a layman. Follow `docs/layman-guide.md`.
Do not rewrite this doc during coding. If the build drifts from what's written
here, add a decision log entry instead.
-->

## Quick summary

- **What:** grow the interest test from 20 fixed questions to a **bank of 300**. Each student gets a **set of 40** from it, and can swap to a fresh set.
- **Why:** with one fixed list, a student who retakes the test sees the same questions again. Their answers get less honest, and the test gets boring.
- **For who:** SPM leavers taking or retaking the interest test.
- **Done when:** every time a student starts the test, they get 40 questions they haven't seen before, and their chart comes only from a fully answered set.
- **Status:** Draft (2026-09-14). Waiting for the product owner's approval.

---

## 1. What problem are we solving?

Today every student gets the same 20 questions, in the same order. A student who retakes the test remembers the questions, so they may answer from memory instead of thinking fresh. 20 questions is also a small sample for 9 interest areas.

> **Example:** Aisyah takes the test in June, then again in August after an open day. She sees the exact same 20 questions. She clicks through fast and her chart barely changes, even though her interests did.

## 2. Who is this for?

Also called: **user stories**.

1. **A student taking the test for the first time** wants **40 varied questions** so their interest chart is **based on enough answers**.
2. **A student coming back to a part-finished test** wants to **carry on with the same questions and saved answers** so they **don't lose progress**.
3. **A student retaking the test** wants **questions they haven't seen** so their answers are **fresh and honest**.
4. **A student who dislikes their current questions** wants to **swap to a new set** so they can **start over with different questions**.

## 3. What we're building

Also called: **scope**.

- **A question bank of 300 questions:** the 20 current approved questions, plus **280 new ones**.
  - Same shape as today: each question has 4 answers, each tagged to a **different** interest area, plus "None of the above".
  - The 9 areas are spread evenly across the bank.
- **A 40-question set per student.** It's picked from the bank when the student starts the test.
  - All **40 questions must be answered** before the interest chart and "likely to love" list appear.
  - Each set is **balanced**: every area shows up in a fair share of its questions.
- **Fresh questions each time.** A new set uses questions the student hasn't been given before. Only when the bank runs out do older questions come back.
- **Opening the Interest Test page:**
  1. **No set yet:** the student gets a new set.
  2. **Set part-answered:** the student carries on with the same set and their saved answers. (Same as today.)
  3. **Set fully answered:** the student gets a new set. Their finished results **stay on My Results** until they finish the new set.
- **A "Get new questions" button**, also called **rotate**.
  - It throws away the current unfinished set, including its answers, and gives a new set.
  - If the student has answered any questions, the page asks them to confirm first.
  - Results from an earlier finished set are not touched.
- **A new server request for rotating** (see T2 below), and a request that returns the student's current set.

## 4. What we're NOT building (on purpose)

Also called: **non-goals** or **out of scope**.

- **Admin screens to edit questions**, because questions still come from an approved file, like the rest of the reference data.
- **Letting students pick how many questions** they get, because a fixed 40 keeps every chart equally reliable.
- **A history of past sets or old charts**, because students only need their latest result.
- **A limit on how often a student can rotate**, because rotating can't raise a score. It only swaps questions.
- **Malay-language questions**, because the site is English-only for now (main PRD section 4).
- **Changing the 20 current questions**, because they're already approved.

> **Why this matters:** writing this down stops the project from quietly growing bigger than planned.

## 5. How we'll know it's done

Also called: **acceptance criteria**.

| # | It's done when... | How we check |
|---|---|---|
| 1 | The bank holds exactly 300 questions. Each has 4 answers in 4 different areas, plus "None of the above". No two questions have the same text | Automated test on the data file |
| 2 | Across the bank, every area is tagged 133 or 134 times | Automated test on the data file |
| 3 | A new set always has 40 different questions, and every area appears in 16 to 20 of them | Automated test over 500 sets |
| 4 | A new set shares no questions with the student's earlier sets, until fewer than 40 unseen questions are left | Automated test |
| 5 | Reopening a part-answered set gives the same 40 questions, in the same order, with saved answers | Automated test, then try it by hand |
| 6 | Reopening after finishing gives a new set, and My Results still shows the finished set's charts | Automated test, then try it by hand |
| 7 | Rotating clears the unfinished set's answers and gives a new set. The page asks first if any answers exist | Automated test, then try it by hand |
| 8 | An answer to a question that isn't in the student's current set is rejected | Automated test |
| 9 | The interest chart only appears once all 40 are answered, and area scores use that set's own counts (T1) | Golden tests with hand-worked numbers |
| 10 | Student A can't see, answer, or rotate student B's set. Deleting an account removes all its sets and answers | Automated test |
| 11 | All 280 new questions were approved by the product owner before being loaded, and the data file says who approved them and how | Check the file and the chat record |
| 12 | The page shows "N of 40 answered", and the rotate button and confirm step work at phone and laptop width | Try it by hand in a browser |

## 6. Rules and limits

Also called: **constraints**.

- **Questions are approved before loading.** New questions are drafted, then reviewed and approved by the product owner. Nothing is marked "approved" without that.
- **Scores still come from code, never AI.** The same set and answers always give the same chart (main PRD section 6).
- **Don't reveal the areas.** Question requests never show which answer maps to which area (main PRD T6).
- **Privacy (PDPA 2010).** Keep only the answers still needed: the current set and the latest finished set. Older answers are deleted. Deleting an account deletes everything (main PRD T4).
- **Keep existing question ids.** The 20 current questions keep their database ids, so the new bank loads without wiping them.
- **Golden test numbers only change on purpose.** The new expected numbers are worked out by hand from the rules.

## 7. Decisions already made

| Decision | Why we chose it |
|---|---|
| Bank of 300 questions: the 20 current + 280 new | The product owner asked for it (2026-09-14) |
| 40 questions per set, all compulsory | More answers give a more reliable interest chart |
| A finished set gets replaced by a new set the next time the page opens | The product owner wants a new set every time the test is opened. A part-finished set is still resumed |
| Finished results stay until the new set is finished | Opening the page shouldn't wipe a student's chart |
| Rotating discards the unfinished set's answers | Answers belong to one set. Mixing sets would make scores unfair |
| Area score = picks ÷ how many questions **in the student's set** offer that area | Each set is different, so the "most picks possible" must come from that set |
| Students with old 20-question answers start again with a 40-question set | Old answers don't belong to any set. The app has no real users yet, so nobody loses real results |

## 8. Questions we still need to answer

- [ ] How does the product owner want to review the 280 new questions? Suggested: in chat, in **7 batches of 40**, each shown as a table.
- [ ] Is 16–20 appearances per area in a set balanced enough? A perfectly even set isn't possible, because 40 × 4 answers = 160 tags, which doesn't split evenly across 9 areas.

---

## Words to know

| Word | What it means here |
|---|---|
| Question bank | All 300 approved questions the sets are picked from |
| Set | The 40 questions one student is given for one attempt at the test |
| Rotate | Swap the current unfinished set for a new one |
| Tag | The interest area an answer counts towards |
| Balanced set | A set where each area shows up in a similar number of questions |
| Resume | Carry on a part-finished set, with saved answers |
| API / endpoint | A request the website sends to the server, like "give me my questions" |
| Golden test | A test with fixed sample inputs and hand-worked expected answers. If a number changes, the test fails |
| PDPA | Personal Data Protection Act 2010, Malaysia's data privacy law |

## Where this fits

**Roadmap phase:** Phase 9, Interest test rotation (to be added to `docs/product-roadmap.md` once this PRD is agreed).

| Related doc | What it tells you |
|---|---|
| `docs/product-roadmap.md` | When this gets built, compared to other work |
| `docs/plan/interest-test-rotation-plan.md` | How we'll build it |
| `docs/prd/furtherxpert-prd.md` | The main rules this feature changes (section 3, T1, T6) |
| `docs/furtherxpert-workflow.md` | How it works once it's built (Flow 3 and Flow 4) |
| `docs/reference/folder-structure.md` | Where its files live in the project |
| `docs/decisions/0004-*.md`, `0008-*.md` | Earlier interest test decisions this feature builds on |

---

## Technical details (for the person building this)

### T1. Scoring changes

- The interest chart uses the student's **latest finished set** only.
- **Area score** = the student's picks for that area in that set ÷ the number of questions in that set that offer the area × 100.
- "None of the above" still counts for nothing. Each answer still has exactly one area.
- If the student has no finished set, Chart 2 shows all 9 areas at 0, and "likely to love" is empty. (Same as a part-finished test today, decision `0008`.)
- Subject strengths, "likely to excel", and eligibility don't change.

### T2. Requests (API)

| Request | Purpose |
|---|---|
| `GET /me/interest-test` | The student's current set: 40 questions with their answers (no areas), plus saved answers and progress. Creates a new set if there's none, or if the latest one is finished |
| `POST /me/interest-test/rotate` | Throw away the current unfinished set and its answers, and return a new set in the same shape |
| `GET /me/interest-answers` | Saved answers and progress for the current set. It never creates a set |
| `PUT /me/interest-answers` | Save answers, merged into what's saved (decision `0008`). Only questions in the current set are accepted |

The public `GET /interest-test` (the whole fixed list) is removed, because there's no longer one list for everyone.

### T3. Set rules

- **Size:** 40 different questions.
- **Balance:** every area appears in 16 to 20 of the 40 questions.
- **Freshness:** use questions the student has never been given first. If fewer than 40 are left, use all of them, then top up with questions seen longest ago, but never from the set just before.
- **What counts as "given":** any set the student received, including rotated-away ones.
