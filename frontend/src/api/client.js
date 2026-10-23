// Every call from the browser to our backend goes through apiFetch().
//
//   const genres = await apiFetch('/genres')
//   const me = await apiFetch('/users/me')
//   await apiFetch('/me/likes', { method: 'PUT', body: { tmdb_id: 27205, value: 1 } })
//   const { access_token } = await apiFetch('/auth/login', { method: 'POST', body, auth: false })
//
// It adds "/api" and the login token, sends the body as JSON, and returns the
// answer as JSON (or null for "204 No Content"). Anything that is not a success
// throws an ApiError with a sentence a person can read.
//
// A 401 on a call that carried a token means the login has expired or is no
// longer valid: the token is removed and the browser goes to /login. Log in and
// sign up pass { auth: false }: there, a 401 only means "wrong email or password".

const TOKEN_KEY = 'cinematch.token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status // 0 when the server could not be reached at all
  }
}

const UNREACHABLE = 'CineMatch cannot reach its server. Check that it is running, then try again.'

// Used when the backend sends no sentence of its own. An empty 502, 503 or 504
// comes from the Vite dev server when our backend is down. (When TMDB is down,
// the backend sends its own 502 with a sentence, which is used instead.)
const FALLBACK = {
  400: 'The request was not accepted.',
  404: 'That could not be found.',
  422: 'Some of the details are not valid.',
  500: 'Something went wrong on the server. Try again.',
  502: UNREACHABLE,
  503: UNREACHABLE,
  504: UNREACHABLE,
}

// FastAPI answers {"detail": "a sentence"}, or {"detail": [{"msg": ...}]} when
// the input is not valid.
async function messageFrom(response) {
  try {
    const { detail } = await response.json()
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  } catch {
    // no JSON body: fall through
  }
  return FALLBACK[response.status] ?? `The server answered ${response.status}.`
}

export async function apiFetch(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { Accept: 'application/json' }
  const token = auth ? getToken() : null
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, UNREACHABLE)
  }

  if (response.status === 401 && token) {
    clearToken()
    if (window.location.pathname !== '/login') window.location.assign('/login')
    throw new ApiError(401, 'Your login has expired. Log in again.')
  }
  if (!response.ok) throw new ApiError(response.status, await messageFrom(response))
  if (response.status === 204) return null
  return response.json()
}
