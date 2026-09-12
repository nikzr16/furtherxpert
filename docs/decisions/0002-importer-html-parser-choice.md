# 0002 - Importer HTML Parser Choice

> **Date:** 2026-09-12 | **Status:** Accepted

<!-- AI Context
Role: This is an append-only record of a single implementation divergence.
Each entry captures why the deviation happened and what it affects.
Never edit an existing decision log entry. To reverse a previous decision,
create a new entry that references the original. After adding an entry,
check the impact checklist below and update affected workflow or reference
docs before the session ends.
-->

## Context

Phase 3's importer (`backend/app/importer/epanduan.py`) reads the live
UPUOnline e-Panduan site page by page and pulls program data out of the raw
**HTML** (the markup a web page is written in) it gets back. To do that it
needs an **HTML parser**: a library that turns that raw HTML text into a
structure the code can search and read. The plan's Open Questions section
left the specific library as a choice for whoever built Phase 3, naming
**selectolax** or **BeautifulSoup** as the two candidates, and asked for the
choice to be written down here.

## Decision

The importer uses **selectolax** (`backend/pyproject.toml`:
`selectolax>=0.4.11`) to parse both the e-Panduan list pages and the
`modalSyarat` **AJAX** (a mini network call a web page makes) fragments that
carry each program's detailed entry requirements.

## Reason

**selectolax** was chosen over **BeautifulSoup** for two reasons:

- **Matches how e-Panduan pages are structured.** The site puts each
  program's detail blocks in separate `<div>` elements identified by
  **id** (a unique tag on one HTML element), for example
  `maklumatProgram__<CODE>`, `kampus__<CODE>`, `laluan-kerjaya_<CODE>`, and
  `syarat-am-<CODE>`. selectolax's `css_first("#some-id")` **CSS selector**
  (a short pattern used to pick out one element, the same syntax used in
  stylesheets) call is a direct, one-line way to grab exactly that element by
  its id. BeautifulSoup can do the same lookup, but selectolax's API reads
  closer to plain CSS and needed no extra parser backend to be installed.
- **Parses faster over many sequential requests.** The importer fetches
  roughly 400+ program pages and detail fragments one at a time, with a
  built-in delay between requests (`REQUEST_DELAY_SECONDS`) so it doesn't
  hammer the real site. selectolax is built on the **Lexbor** HTML engine (a
  fast C library), which parses each page noticeably quicker than
  BeautifulSoup's Python-level parsing. That speed doesn't change how long
  the whole run takes -- the request delay dominates -- but it keeps
  per-page parsing overhead low and avoids adding a second, slower parsing
  step to a run that already has hundreds of network round trips.

BeautifulSoup remains a reasonable alternative (more familiar to more
developers, more tolerant of malformed markup), but wasn't needed here: the
e-Panduan pages parse cleanly, and the id-based lookups selectolax offers
line up exactly with how this site's markup is built.

## Impact

- [ ] Workflow doc updated
- [x] Reference doc updated (this entry documents the plan's Open Questions
      item; `backend/app/importer/epanduan.py` and
      `backend/pyproject.toml` already reflect the choice, no code change
      needed)
- [x] No upstream doc update needed (the plan's Open Questions item is
      resolved by this entry per its own instructions; the plan itself is
      not edited)
