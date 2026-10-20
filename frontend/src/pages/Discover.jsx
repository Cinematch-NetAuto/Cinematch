// Browse with filters, at /discover. The film picker (FilterPanel) writes the
// filters into the address; this page reads the address, asks the backend and
// shows the films, page by page. A refresh or a shared link shows the same page.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import FilterPanel, { discoverQuery, readFilters } from '../components/FilterPanel.jsx'
import MovieGrid from '../components/MovieGrid.jsx'
import Paginator from '../components/Paginator.jsx'
import { Empty, ErrorMessage, Loading } from '../components/States.jsx'

// TMDB stops counting at 20,001: "every drama ever made" reports that number too.
const TMDB_COUNT_LIMIT = 20001

function countText(total) {
  if (total >= TMDB_COUNT_LIMIT) return 'Over 20,000 films'
  return total === 1 ? '1 film' : `${total.toLocaleString('en')} films`
}

export default function Discover() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number.parseInt(params.get('page'), 10) || 1)
  const perPage = params.get('per_page') === '20' ? 20 : 10
  const query = discoverQuery(readFilters(params), page, perPage)

  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0) // "Try again" bumps this

  useEffect(() => {
    let current = true // an older, slower answer must not overwrite a newer one
    setLoading(true)
    setError('')
    apiFetch(query)
      .then((answer) => current && setResult(answer))
      .catch((failure) => current && setError(failure.message))
      .finally(() => current && setLoading(false))
    return () => {
      current = false
    }
  }, [query, attempt])

  // Paging keeps the filters; a new page size starts again on page 1.
  function setPaging(changes) {
    setParams((old) => {
      const next = new URLSearchParams(old)
      for (const [key, value] of Object.entries(changes)) {
        if (value === null) next.delete(key)
        else next.set(key, value)
      }
      return next
    })
    document.getElementById('results')?.scrollIntoView()
  }

  function clearFilters() {
    setParams(perPage === 20 ? { per_page: '20' } : {})
  }

  return (
    <>
      <h1>Discover</h1>
      <FilterPanel />

      <section id="results" aria-label="Films">
        {loading && <Loading count={perPage} />}
        {!loading && error && <ErrorMessage message={error} onRetry={() => setAttempt((n) => n + 1)} />}
        {!loading && !error && result?.results.length === 0 && (
          <Empty
            title="No films match those filters."
            action={
              <button type="button" className="button" onClick={clearFilters}>
                Clear filters
              </button>
            }
          >
            Try a wider release period or a lower rating.
          </Empty>
        )}
        {!loading && !error && result?.results.length > 0 && (
          <>
            <p className="search-hint" role="status">
              {countText(result.total_results)}
            </p>
            <MovieGrid films={result.results} />
            <Paginator
              page={result.page}
              totalPages={result.total_pages}
              perPage={perPage}
              onPage={(n) => setPaging({ page: n })}
              onPerPage={(n) => setPaging({ per_page: n, page: null })}
            />
          </>
        )}
      </section>
    </>
  )
}
