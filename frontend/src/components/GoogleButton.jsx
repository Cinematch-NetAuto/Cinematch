// The "Sign in with Google" button, from the @react-oauth/google package.
//
// The backend says which Google client ID to use (GET /api/auth/google), so the
// ID is set in one place: GOOGLE_CLIENT_ID in .env. With no ID, or when Google's
// script cannot load (offline), nothing is shown and email login still works.
// After a sign-in, onCredential(token) gets Google's ID token.
import { useEffect, useState } from 'react'
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google'
import { apiFetch } from '../api/client.js'

export default function GoogleButton({ onCredential, onError }) {
  const [clientId, setClientId] = useState('')
  const [scriptFailed, setScriptFailed] = useState(false)

  useEffect(() => {
    let current = true
    apiFetch('/auth/google', { auth: false })
      .then(({ client_id: id }) => current && setClientId(id))
      .catch(() => {}) // no answer from the backend: no Google button
    return () => {
      current = false
    }
  }, [])

  if (!clientId || scriptFailed) return null
  return (
    <GoogleOAuthProvider clientId={clientId} onScriptLoadError={() => setScriptFailed(true)}>
      <p className="form-or">or</p>
      <div className="google-button">
        <GoogleLogin onSuccess={(response) => onCredential(response.credential)} onError={onError} />
      </div>
    </GoogleOAuthProvider>
  )
}
