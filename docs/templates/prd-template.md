# [Feature name]

> **What kind of doc is this?** A product brief, also called a **PRD** (Product Requirements Document). It says **what** we're building and **why**. It does not say how.
>
> **Keep it updated?** No. If plans change while building, don't edit this doc. Add a note to the decision log (`docs/decisions/`) instead.

<!-- AI Context
Role: This doc captures what the feature should do and why. For how to build it,
read the plan in `docs/plan/`.
Reader: a layman, meaning a junior developer or a non-technical person, who may
have ADHD. Write in layman terms and follow `docs/layman-guide.md`: point first,
short sentences, lists, and every technical term explained the first time it
appears.
Do not rewrite this doc during coding. If the build drifts from what's written
here, add a decision log entry instead.
When filling this in: replace every _italic hint_ and delete the example
callouts. Keep the "Also called" lines, because they teach the technical name.
-->

## Quick summary

- **What:** _One sentence. What are we building?_
- **Why:** _One sentence. What problem does it fix?_
- **For who:** _Who will use it?_
- **Done when:** _The single most important sign that it works._
- **Status:** _Draft / Agreed / Building / Shipped_

---

## 1. What problem are we solving?

_2–3 short sentences. Describe the problem the way the user feels it. Don't describe the fix yet._

> **Example:** Users who forget their password get locked out. They have to email support and wait up to 1 day to get back in.

## 2. Who is this for?

Also called: **user stories**.

_One line per type of user. Use this pattern:_

1. **[Who]** wants to **[do something]** so they can **[get some result]**.

> **Example:** **A logged-out user** wants to **reset their password by email** so they can **get back in without waiting for support**.

## 3. What we're building

Also called: **scope**.

_The things this feature includes. One item per bullet, in plain words._

- ...

## 4. What we're NOT building (on purpose)

Also called: **non-goals** or **out of scope**.

_Things someone might expect, but we're leaving out. Add a short reason for each._

- ... because ...

> **Why this matters:** writing this down stops the project from quietly growing bigger than planned.

## 5. How we'll know it's done

Also called: **acceptance criteria**.

_Each row is one thing someone can check. If it can't be checked, rewrite it until it can._

| # | It's done when... | How we check |
|---|---|---|
| 1 | _A user gets the reset email within 1 minute._ | _Automated test / Try it by hand / Measure it_ |

## 6. Rules and limits

Also called: **constraints**.

_Things we must follow or can't change. For example: deadlines, budget, tools we must use, laws, or "don't touch X"._

- ...

## 7. Decisions already made

_Choices that are settled, and why. This stops people re-arguing them later._

| Decision | Why we chose it |
|---|---|
| | |

## 8. Questions we still need to answer

_Anything unclear. Say who can answer it, if you know._

- [ ] ...

---

## Words to know

_Every technical word used in this doc, explained in plain words. Delete this section only if the doc has no technical words._

| Word | What it means here |
|---|---|
| | |

## Where this fits

**Roadmap phase:** _[Phase number and name from `docs/product-roadmap.md`]_

| Related doc | What it tells you |
|---|---|
| `docs/product-roadmap.md` | When this gets built, compared to other work |
| `docs/plan/[feature]-plan.md` | How we'll build it |
| `docs/[feature]-workflow.md` | How it works once it's built |
| `docs/reference/folder-structure.md` | Where its files live in the project |
| `docs/decisions/NNNN-*.md` | What changed from this doc while building, and why |
