// Log in, at /login. After logging in you go back to the page that sent you
// here (location.state.from), or to Home. A logged-in visitor goes straight on.
import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { user, login } = useAuth()
  const location = useLocation()
  const goTo = location.state?.from || '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={goTo} replace />

  async function handleSubmit(event) {
    event.preventDefault()
    if (!email.trim() || !password) {
      setError('Enter your email and password.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await login(email.trim(), password) // on success `user` is set and we move on
    } catch (failure) {
      setError(failure.message) // for example "Invalid email or password"
      setBusy(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Log in</h1>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span className="field-label">Email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="field-label">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p>
        No account yet?{' '}
        <Link to="/register" state={location.state}>
          Sign up
        </Link>
      </p>
    </section>
  )
}
