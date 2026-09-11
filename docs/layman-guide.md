# Layman Writing Guide

> **Quick summary**
> - This harness writes everything in **layman terms**: words anyone can understand, not just experts.
> - Every doc and chat message is for a **junior developer or a non-technical reader**.
> - Assume the reader may have **ADHD**. They skim, lose focus in long text, and need the point fast.
> - So: **point first, short chunks, plain words, every technical term explained.**
> - This file is the rulebook for writing. If another file disagrees about style, this file wins.

---

## 1. Who we're writing for

A **layman** is someone who isn't an expert in the topic. That's who we write for:

- **A junior developer.** Knows basic coding. Doesn't know architecture words yet.
- **A non-technical person.** A client, manager, or designer who needs to know what's going on.
- **Someone who skims.** ADHD or not, most people skim first.

**The test:** all 3 should understand the Quick summary. The first 2 should be able to follow the whole doc.

> **Why the name:** this is the **layman harness**. Writing in layman terms is its main job, not an extra.
> Outside this project, the same idea is often called **plain language**.

---

## 2. The 10 rules

1. **Point first.** Start with the answer or the summary. Details come after.
2. **Short sentences.** Aim for 15 words. Never more than 25.
3. **Short chunks.** Max 3 sentences per paragraph. Then use a break, a list, or a heading.
4. **Lists over paragraphs.** 3 or more items? Use bullets. Order matters? Number them.
5. **Plain words.** Write "use", not "utilize". See the word swap list in section 7.
6. **Explain every technical term the first time.** Plain meaning first, then the term in bold.
7. **Spell out every acronym the first time.** "PRD (Product Requirements Document)".
8. **Say who does what.** "The app sends an email", not "An email is sent".
9. **Give an example** for anything abstract.
10. **One word per idea.** Pick a term and stick with it. Don't swap in synonyms for variety.

---

## 3. How to explain a technical term

**Pattern:** say it in plain words first, then give the real name in bold.

| Don't write | Write |
|---|---|
| We use exponential backoff. | If a request fails, we try again. We wait longer each time: 1s, 2s, 4s. This is called **exponential backoff**. |
| The endpoint is idempotent. | Sending the same request twice gives the same result as sending it once. So nobody gets charged twice. This is called **idempotent**. |
| Run the migration first. | First, update the database's layout to match the new code. This is called a **migration**. |

**Keep the technical term when** the reader will meet it again: in code, error messages, tools, or other docs. Explain it once, then use it. Add it to the doc's **Words to know** section.

**Drop the technical term when** a plain word does the same job and nobody needs the real name.

---

## 4. Layout: make it easy to skim

These help every reader, and they matter most for readers with ADHD.

**Every doc has:**
- A **Quick summary** box at the top, with 3–5 bullets. Cover what, why, who, and what's next.
- **Headings** at least every 10 lines. Use plain labels or questions ("How we'll know it's done").
- **Numbered sections** in long docs, so readers can find their place again.
- A clear **Next step** at the end, if someone needs to do something.

**Use:**
- **Bold** on 1–2 key words per chunk. Never bold whole sentences.
- **Tables** to compare things (options, before/after, who does what).
- **Checklists** (`- [ ]`) for anything someone must do.
- **Digits** for numbers: "3 steps", not "three steps".
- **Callouts** from this fixed set only, so they look the same everywhere:
  - `> **Why this matters:** ...`
  - `> **Watch out:** ...`
  - `> **Example:** ...`
  - `> **Next step:** ...`

**Avoid:**
- Walls of text.
- Long stretches of *italic* or ALL CAPS.
- Brackets inside brackets.
- Footnotes, and "see above" or "see below". Link to the section or repeat the point instead.

---

## 5. Plain first, exact details second

Some docs need exact details: file names, commands, settings. The person building the thing needs them, so **keep them**. But:

- Put them in a clearly labelled section, like **"Technical details (for the person building this)"**.
- Write that section plainly too. Short sentences. Explain terms.
- Put code, file paths, and commands in `code format`. **Never** reword them. Being exact there is not jargon.

> **Why this matters:** a beginner can stop reading before the technical section and still understand the doc. The builder still gets every detail they need.

---

## 6. Chat replies and status updates

**Every chat reply** follows these rules, not just docs. That includes answers, explanations, and progress updates. Keep chat even shorter than docs.

- **Answer first.** The first line is the answer or the result.
- **Say what's happening in plain words.** Leave out internal names like agent names, step ids, and tier letters. Only mention them if the user asks.
- **1–3 lines** per update.
- **End with what's next**, or with what you need from the user.

| Don't write | Write |
|---|---|
| Execution tier: F — Fast lane. Spawning executor; review gate verdict contract APPROVE/REVISE. | This is a small change, so I'll use the quick process. Making the change now, then I'll check it for mistakes. |
| VERDICT: BLOCK — acceptance criterion 2 unmet. | I stopped. The "reset email arrives within 1 minute" check failed. I need to fix that before moving on. |

---

## 7. Word swap list

| Instead of | Write |
|---|---|
| utilize, leverage | use |
| implement | build, add |
| facilitate | help, make easier |
| mitigate | reduce, lower the risk of |
| functionality | feature, what it does |
| prior to | before |
| in order to | to |
| subsequently | then, later |
| commence / terminate | start / stop |
| optimize | make faster, make cheaper (say which) |
| robust | reliable, hard to break |
| scalable | can handle more users or data (say how many) |
| stakeholders | the people involved (name them) |
| requirements | what it must do |
| constraints | rules and limits |
| dependencies | what this relies on |
| edge case | unusual situation (give an example) |
| latency | delay, wait time |
| granular | detailed |
| persist | save |
| payload | the data being sent |
| instantiate | create |
| e.g. / i.e. / etc. | for example / that is / list the items |

**Always explain these the first time.** Keep the word, because readers will see it again:

API, database, endpoint, server, frontend, backend, deploy, environment variable, migration, cache, authentication, authorization, webhook, repository, branch, merge, pull request, CI (Continuous Integration), unit test, integration test.

---

## 8. Before and after

**Before:**

> The service implements idempotent webhook handling with exponential backoff to mitigate transient upstream failures, ensuring robust payment reconciliation.

**After:**

> **What this does:** it makes sure payments are recorded correctly, even when something goes wrong.
>
> - Sometimes the payment provider's server has a short hiccup, and our request fails.
> - When that happens, we try again. We wait a bit longer each time: 1s, 2s, 4s. This is called **exponential backoff**.
> - If the same payment message arrives twice, we only record it once. So nobody gets charged twice. This is called being **idempotent**.

---

## 9. Self-check before you finish

- [ ] Quick summary at the top, with 3–5 bullets?
- [ ] Would a non-technical reader understand the summary?
- [ ] Every technical term explained the first time it appears?
- [ ] Every acronym spelled out the first time?
- [ ] No sentence longer than 25 words?
- [ ] No paragraph longer than 3 sentences?
- [ ] 3 or more items written as a list?
- [ ] Clear next step at the end, if someone has to act?
