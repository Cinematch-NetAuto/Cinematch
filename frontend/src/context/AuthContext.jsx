// Who is logged in, for the whole app.
//
//   const { user, checking, login, register, logout } = useAuth()
//
// The login token lives in the browser (see api/client.js), so a refresh keeps
// you logged in: on start, if a token is saved, we ask the backend who it
// belongs to. While that question is open, `checking` is true.
//
// <RequireAuth /> guards the /me/... pages: a logged-out visitor is sent to
// /login, which can send them back afterwards (location.state.from).
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { apiFetch, clearToken, getToken, setToken } from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(() => Boolean(getToken()))

  // On start: if a token is saved, find out whose it is. A 401 (expired token)
  // is handled inside apiFetch: it removes the token and goes to /login.
  useEffect(() => {
    if (!getToken()) return
    let current = true
    apiFetch('/users/me')
      .then((me) => current && setUser(me))
      .catch(() => current && setUser(null))
      .finally(() => current && setChecking(false))
    return () => {
      current = false
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const { access_token } = await apiFetch('/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    })
    setToken(access_token)
    const me = await apiFetch('/users/me')
    setUser(me)
    return me
  }, [])

  // Create the account, then log in with the same details.
  const register = useCallback(
    async ({ displayName, email, password, genreIds }) => {
      await apiFetch('/auth/register', {
        method: 'POST',
        body: { display_name: displayName, email, password, genre_ids: genreIds },
        auth: false,
      })
      return login(email, password)
    },
    [login],
  )

  const googleLogin = useCallback(async (credential, genreIds = null) => {
    const body = { credential }
    if (genreIds) body.genre_ids = genreIds

    const { access_token } = await apiFetch('/auth/google', {
      method: 'POST',
      body,
      auth: false,
    })
    setToken(access_token)
    const me = await apiFetch('/users/me')
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, checking, login, register, googleLogin, logout }),
    [user, checking, login, register, googleLogin, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth() must be used inside <AuthProvider>')
  return auth
}

// Wraps the routes that need a login.
export function RequireAuth() {
  const { user, checking } = useAuth()
  const location = useLocation()
  if (checking) return <p role="status">Checking your login…</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
