# 0001 - Test Database Isolation Strategy

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

Phase 2 (accounts) needed automated tests for `POST /auth/register`,
`POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /me`, and
`DELETE /me` (PRD T3, T4). To be trustworthy, these tests had to exercise the
real **PostgreSQL** database rules, not a stand-in: the unique-email rule, the
`race` and `spm_year` **CHECK constraints** (database-level rules that reject
bad values), and the real Alembic **migration** (the script that builds the
`users` table) -- not just a Python model recreated in memory.

At the same time, tests must never write to, or leave leftover rows in, the
developer's own database (the one Docker Compose starts for local work).

## Decision

Tests that touch the database (`backend/tests/test_auth.py`) run against a
dedicated `sambungbelajarmu_test` Postgres database on the same Postgres
server used for local development, not the dev database itself:

- The test database is created automatically on first run if it doesn't
  exist yet. `conftest.py` refuses to run unless the database name ends in
  `_test`, so it can never accidentally point at a real database.
- `alembic upgrade head` (the command that applies all migrations) runs once
  per test session against that database, so tests run against the actual
  migration output, not a shortcut copy of the table shapes.
- Every single test runs inside one outer database **transaction** (a
  reversible batch of changes) plus a nested **savepoint** (a bookmark inside
  that transaction that can be rolled back on its own, using SQLAlchemy's
  `join_transaction_mode="create_savepoint"`). Because of this, when the
  application code calls `commit()` (as `POST /auth/register` and
  `DELETE /me` do), that commit only releases the savepoint -- it does not
  leave the outer transaction. After the test finishes, the whole outer
  transaction is rolled back, so nothing the test did is ever kept.

This was checked empirically: the developer's `users` table had 0 rows
before and 0 rows after a full test run.

## Reason

Two other approaches were considered and rejected for this project:

- **A fully mocked or in-memory database** (for example SQLite in place of
  Postgres, or a fake session object) would be faster to run, but would not
  enforce the same rules as production. SQLite doesn't support the
  Postgres-specific `CHECK` constraints and **UUID** (a random, unique ID
  format) column type used here, so a bug in the `race` or `spm_year` rule,
  or in the real migration file, could pass the tests and still break in
  production.
- **A fresh, throwaway Postgres container per test run** (spinning up a new
  Docker container just for tests, then destroying it) gives full isolation
  and is closest to production, but adds real setup cost and slows down
  every run with container start-up time. The project already runs a
  Postgres server via `docker-compose.yml` for local development, so reusing
  that running server with one dedicated `_test` database gets almost the
  same isolation guarantee for a fraction of the machinery.

The transaction-plus-savepoint technique closes the remaining gap: even
though tests share the real server and the real `users` table, no test can
ever leave data behind or interfere with another test, because every change
is undone right after the test ends.

## Impact

- [x] Reference doc updated (`docs/reference/folder-structure.md`: `tests/conftest.py`
      entry now notes the real, separate test database)
- [ ] Workflow doc updated
- [x] No upstream doc update needed (no accounts workflow doc exists yet to update)
