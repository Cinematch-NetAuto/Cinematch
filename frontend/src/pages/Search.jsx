// Title search, at /search. Results appear as you type, 300 ms after the last
// key, so typing "inception" sends one request, not nine.
//
// The search word lives in the address (/search?q=inception): a refresh, the
// Back button or a shared link shows the same results.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import MovieGrid from '../components/MovieGrid.jsx'
import { Empty, ErrorMessage, Loading } from '../components/States.jsx'

const PAUSE_MS = 300
const PER_PAGE = 20

export default function Search() {
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const [typed, setTyped] = useState(query)
  const [result, setResult] = useState(null) // { films, total } after a search
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [attempt, setAttempt] = useState(0) // "Try again" bumps this

  // The address changed by itself (Back button, a link): show its word in the box.
  // Only when it really differs, so a space you just typed is not wiped out.
  useEffect(() => {
    setTyped((text) => (text.trim() === query ? text : query))
  }, [query])

  // Copy the typed text into the address once the typing pauses.
  useEffect(() => {
    const wait = setTimeout(() => {
      const word = typed.trim()
      if (word !== query) setParams(word ? { q: word } : {}, { replace: true })
    }, PAUSE_MS)
    return () => clearTimeout(wait)
  }, [typed, query, setParams])

  // Search whenever the word in the address changes.
  useEffect(() => {
    if (!query) {
      setResult(null)
      setError('')
      setLoading(false)
      return
    }
    let current = true // an older, slower answer must not overwrite a newer one
    setLoading(true)
    setError('')
    apiFetch(`/movies/search?q=${encodeURIComponent(query)}&page=1&per_page=${PER_PAGE}`)
      .then((page) => current && setResult({ films: page.results, total: page.total_results }))
      .catch((failure) => current && setError(failure.message))
      .finally(() => current && setLoading(false))
    return () => {
      current = false
    }
  }, [query, attempt])

  return (
    <>
      <h1>Search</h1>
      <label className="field search-field">
        <span className="field-label">Film title</span>
        <input
          type="search"
          placeholder="Inception"
          maxLength={100}
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          autoFocus
        />
      </label>

      {!query && <p className="search-hint">Type a film title to search.</p>}
      {query && loading && <Loading count={6} label="Searching" />}
      {query && !loading && error && (
        <ErrorMessage message={error} onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {query && !loading && !error && result && result.films.length === 0 && (
        <Empty title={`No films found for "${query}".`}>
          Check the spelling or try fewer words.
        </Empty>
      )}
      {query && !loading && !error && result && result.films.length > 0 && (
        <>
          <p className="search-hint" role="status">
            {result.total === 1 ? '1 film found' : `${result.total} films found`}
            {result.total > result.films.length && `, showing the first ${result.films.length}`}
          </p>
          <MovieGrid films={result.films} />
        </>
      )}
    </>
  )
}
