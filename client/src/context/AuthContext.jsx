// Login state (PRD T3, proj-auth-security skill; plan Phase 6 task 1).
//
// The access token lives in memory only, in this React context -- NEVER in
// localStorage/sessionStorage. On app load we try a silent /auth/refresh
// (the refresh token lives in an httpOnly cookie the browser sends
// automatically with credentials: "include"). Any authenticated call goes
// through `authedFetch`, which attaches the bearer token and retries once
// via refresh on a 401 before giving up.

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { loginAccount, logoutAccount, refreshAccessToken } from '../api'

const API_BASE_URL = import.meta.env.VITE_API_URL

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null)
  const [initializing, setInitializing] = useState(true)
  // authedFetch is called from event handlers/effects, sometimes right after
  // a token update -- a ref keeps it reading the latest token without
  // recreating the callback on every change. Updated in an effect, not
  // during render, so render stays a pure function of state.
  const tokenRef = useRef(null)
  useEffect(() => {
    tokenRef.current = accessToken
  }, [accessToken])

  const trySilentRefresh = useCallback(async () => {
    try {
      const data = await refreshAccessToken()
      setAccessToken(data.access_token)
      return data.access_token
    } catch {
      setAccessToken(null)
      return null
    }
  }, [])

  useEffect(() => {
    trySilentRefresh().finally(() => setInitializing(false))
  }, [trySilentRefresh])

  const login = useCallback(async (email, password) => {
    const data = await loginAccount(email, password)
    setAccessToken(data.access_token)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutAccount()
    } finally {
      setAccessToken(null)
    }
  }, [])

  // Every authenticated call in the app goes through here.
  const authedFetch = useCallback(
    async (path, { method = 'GET', body, noContent = false } = {}) => {
      const doFetch = (token) =>
        fetch(`${API_BASE_URL}${path}`, {
          method,
          credentials: 'include',
          headers: {
            ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: body !== undefined ? JSON.stringify(body) : undefined,
        })

      let response = await doFetch(tokenRef.current)

      // 401 = not logged in (or the access token just expired): retry once
      // via refresh, then give up and let the caller send the student to
      // Login (plan Phase 6 task 1).
      if (response.status === 401) {
        const newToken = await trySilentRefresh()
        if (!newToken) {
          const error = new Error('Not logged in')
          error.status = 401
          throw error
        }
        response = await doFetch(newToken)
      }

      if (noContent) {
        if (!response.ok) {
          const error = new Error(`Request failed: ${response.status}`)
          error.status = response.status
          throw error
        }
        return null
      }

      let data = null
      try {
        data = await response.json()
      } catch {
        data = null
      }
      if (!response.ok) {
        const detail = data && data.detail
        const message =
          typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `Request failed: ${response.status}`
        const error = new Error(message)
        error.status = response.status
        error.data = data
        throw error
      }
      return data
    },
    [trySilentRefresh]
  )

  const value = {
    isAuthenticated: accessToken !== null,
    initializing,
    login,
    logout,
    authedFetch,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
