// Backend calls (PRD T6). Base URL comes from VITE_API_URL (see .env.example).
//
// Two kinds of function here:
// - Plain calls (no login needed): subjects/universities/programs/interest
//   test lookup, plus register/login/refresh/logout.
// - Authenticated calls take `authedFetch` (from AuthContext, see
//   src/context/AuthContext.jsx) as their first argument -- it attaches the
//   in-memory access token and retries once via /auth/refresh on a 401
//   (proj-auth-security skill: access token in memory only, never
//   localStorage/sessionStorage; credentials: "include" for the refresh
//   cookie).

const API_BASE_URL = import.meta.env.VITE_API_URL

async function parseResponse(response) {
  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }
  if (!response.ok) {
    const detail = data && data.detail
    const message = typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `Request failed: ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}

async function publicRequest(path, { method = 'GET', body, credentials } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return parseResponse(response)
}

// --- No login needed --------------------------------------------------

export function getHealth() {
  return publicRequest('/health')
}

export function registerAccount(payload) {
  return publicRequest('/auth/register', { method: 'POST', body: payload })
}

export function loginAccount(email, password) {
  return publicRequest('/auth/login', { method: 'POST', body: { email, password }, credentials: 'include' })
}

export function refreshAccessToken() {
  return publicRequest('/auth/refresh', { method: 'POST', credentials: 'include' })
}

export function logoutAccount() {
  return publicRequest('/auth/logout', { method: 'POST', credentials: 'include' })
}

export function getSubjects() {
  return publicRequest('/subjects')
}

export function getUniversities() {
  return publicRequest('/universities')
}

export function getPrograms() {
  return publicRequest('/programs')
}

export function getProgram(code) {
  return publicRequest(`/programs/${encodeURIComponent(code)}`)
}

export function getInterestTestQuestions() {
  return publicRequest('/interest-test')
}

// --- Needs login (authedFetch from AuthContext) -------------------------

export function getMe(authedFetch) {
  return authedFetch('/me')
}

export function deleteMe(authedFetch) {
  return authedFetch('/me', { method: 'DELETE', noContent: true })
}

export function getMyResults(authedFetch) {
  return authedFetch('/me/results')
}

export function putMyResults(authedFetch, items) {
  return authedFetch('/me/results', { method: 'PUT', body: items })
}

export function getMyInterestAnswers(authedFetch) {
  return authedFetch('/me/interest-answers')
}

export function putMyInterestAnswers(authedFetch, items) {
  return authedFetch('/me/interest-answers', { method: 'PUT', body: items })
}

export function getMyAnalysis(authedFetch) {
  return authedFetch('/me/analysis')
}

export function getMyAnalysisSummary(authedFetch) {
  return authedFetch('/me/analysis/summary')
}
