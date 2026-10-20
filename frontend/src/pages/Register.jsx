// Sign up, at /register. You pick at least 3 genres here, so the recommender
// has something to work with from day one (the "cold start"). After signing up
// you are logged in and go to Home.
import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { ErrorMessage } from '../components/States.jsx'
import { useAuth } from '../context/AuthContext.jsx'

// The same rules as the backend (backend/app/schemas.py, UserCreate).
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MIN_GENRES = 3

function check({ displayName, email, password, genreIds }) {
  const problems = {}
  if (!displayName.trim()) problems.displayName = 'Enter your name.'
  else if (displayName.trim().length > 50) problems.displayName = 'Use 50 characters or fewer.'
  if (!EMAIL_PATTERN.test(email.trim())) problems.email = 'Enter an email address like name@example.com.'
  if (password.length < 8) problems.password = 'Use at least 8 characters.'
  else if (password.length > 72) problems.password = 'Use 72 characters or fewer.'
  if (genreIds.length < MIN_GENRES) problems.genres = `Choose at least ${MIN_GENRES} genres.`
  return problems
}

export default function Register() {
  const { user, register } = useAuth()
  const location = useLocation()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [genreIds, setGenreIds] = useState([])
  const [problems, setProblems] = useState({})
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)

  const [genres, setGenres] = useState(null) // null while loading
  const [genresError, setGenresError] = useState('')

  const loadGenres = useCallback(() => {
    setGenresError('')
    apiFetch('/genres')
      .then(setGenres)
      .catch((failure) => setGenresError(failure.message))
  }, [])

  useEffect(loadGenres, [loadGenres])

  if (user) return <Navigate to={location.state?.from || '/'} replace />

  function toggleGenre(id) {
    setGenreIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const details = { displayName, email, password, genreIds }
    const found = check(details)
    setProblems(found)
    setFormError('')
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      await register({ ...details, displayName: displayName.trim(), email: email.trim() })
    } catch (failure) {
      if (failure.status === 409) setProblems({ email: 'That email already has an account.' })
      else setFormError(failure.message)
      setBusy(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Sign up</h1>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span className="field-label">Your name</span>
          <input
            autoComplete="nickname"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            aria-invalid={Boolean(problems.displayName)}
            aria-describedby="name-problem"
          />
          {problems.displayName && <span className="field-error" id="name-problem">{problems.displayName}</span>}
        </label>

        <label className="field">
          <span className="field-label">Email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-invalid={Boolean(problems.email)}
            aria-describedby="email-problem"
          />
          {problems.email && (
            <span className="field-error" id="email-problem">
              {problems.email}
              {problems.email.includes('already') && (
                <>
                  {' '}
                  <Link to="/login">Log in instead</Link>
                </>
              )}
            </span>
          )}
        </label>

        <label className="field">
          <span className="field-label">Password</span>
          <span className="field-hint">At least 8 characters.</span>
          <input
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={Boolean(problems.password)}
            aria-describedby="password-problem"
          />
          {problems.password && <span className="field-error" id="password-problem">{problems.password}</span>}
        </label>

        <fieldset className="field">
          <legend className="field-label">Genres you like</legend>
          <p className="field-hint">
            Choose at least {MIN_GENRES}. We use them for your first recommendations. {genreIds.length} chosen.
          </p>
          {genresError && <ErrorMessage message={genresError} onRetry={loadGenres} />}
          {!genres && !genresError && <p role="status">Loading genres…</p>}
          {genres && (
            <div className="tiles">
              {genres.map((genre) => (
                <button
                  key={genre.id}
                  type="button"
                  className="tile"
                  aria-pressed={genreIds.includes(genre.id)}
                  onClick={() => toggleGenre(genre.id)}
                >
                  {genre.name}
                </button>
              ))}
            </div>
          )}
          {problems.genres && <span className="field-error">{problems.genres}</span>}
        </fieldset>

        {formError && (
          <p className="form-error" role="alert">
            {formError}
          </p>
        )}
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Creating your account…' : 'Create account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login" state={location.state}>Log in</Link>
      </p>
    </section>
  )
}
