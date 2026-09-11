---
name: proj-auth-security
description: SambungBelajarmu.ai login and privacy checklist — stateless JWT (access + refresh), argon2 passwords, rate limiting, per-user data scoping, CORS, PDPA 2010 data minimisation, logging bans, and GPT-5 data limits. Use before building or reviewing auth, /me endpoints, sign-up, account deletion, logging, or the AI summary.
---

# Login and privacy checklist

Source of truth: `docs/prd/sambungbelajarmu-v2-prd.md` T3–T4.

## 1. Tokens (stateless JWT)

| Item | Rule |
|---|---|
| Library | PyJWT, `HS256`, secret from `JWT_SECRET` (≥ 32 random bytes); refuse to start if missing |
| Access token | 15 min (`JWT_ACCESS_MINUTES`); claims `sub` (user id), `type: "access"`, `exp`, `iat` |
| Refresh token | 7 days (`JWT_REFRESH_DAYS`); `type: "refresh"`; set as cookie `httpOnly; Secure; SameSite=Strict; Path=/auth` |
| Validation | always verify signature, `exp`, and `type`; an access token must never work as refresh and vice versa |
| Client storage | access token in memory only (React state/context). **Never** in localStorage or sessionStorage |
| Logout | clear the refresh cookie; client drops the access token |

## 2. Passwords and sign-up

- Hash with argon2 (`argon2-cffi` / `pwdlib[argon2]`). Never store or log plain passwords.
- Minimum 8 characters. Emails are lower-cased and unique.
- Required fields:
  - email, password,
  - `is_citizen` (bool),
  - `race`: one of Melayu, Cina, India, Anak Negeri Sabah, Anak Negeri Sarawak, Orang Asli, Lain-lain,
  - `spm_year`,
  - consent (store `consent_at`).
- The form explains: race is used **only** to check Bumiputera-only programs.
- Login errors are generic ("Wrong email or password"). Never reveal which part was wrong.

## 3. Access control

- Every `/me/*` handler gets the user from the access token dependency, never from a path or body id.
- Every query on student tables filters by that user id.
  - A test must prove user A gets 404/403 on user B's data.
- `DELETE /me` removes the user and all dependent rows (FK `ON DELETE CASCADE`) in one transaction.

## 4. Abuse and transport

- Rate limit with `slowapi`:
  - `/auth/login` and `/auth/register`: 5 per minute per IP.
  - Other endpoints: sensible defaults.
- CORS: `allow_origins=[FRONTEND_ORIGIN]` and `allow_credentials=True`. **Never** use `*`.

## 5. Logging and AI

- Never log request bodies, grades, answers, race, tokens, cookies, or AI prompts/replies.
  - Log only method, path, status, and duration.
- GPT-5 input is limited to area names plus scores and group names plus scores.
  - No email, race, raw grades, or user id.
- An AI call failure returns `summary: null` with a friendly message. It never breaks `/me/analysis`.

## 6. Review checklist

- [ ] Token `type` checked. Expiry enforced. Secret comes from env.
- [ ] Refresh cookie flags are correct. No token in web storage.
- [ ] argon2 used. Login errors are generic.
- [ ] All `/me/*` queries are scoped. The cross-user test exists.
- [ ] Delete cascades everything.
- [ ] Rate limit is on the auth routes. CORS is not `*`.
- [ ] No sensitive data in logs or in the AI payload.
