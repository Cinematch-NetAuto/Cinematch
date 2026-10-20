// Your films, at /me/library, in three tabs: Liked, Disliked and Watched.
// A like or a dislike can be removed here. The open tab lives in the address
// (/me/library?tab=watched), so a refresh or Back keeps it.
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import MovieCard from '../components/MovieCard.jsx'
import { Empty, ErrorMessage, Loading } from '../components/States.jsx'

const TABS = [
  { id: 'liked', label: 'Liked' },
  { id: 'disliked', label: 'Disliked' },
  { id: 'watched', label: 'Watched' },
]

const EMPTY = {
  liked: ['Nothing liked yet.', 'Like a film from its page and it appears here.'],
  disliked: ['Nothing disliked yet.', 'Films you dislike are never recommended to you.'],
  watched: ['Nothing watched yet.', 'Mark a film as watched from its page and it appears here.'],
}

function dateText(iso) {
  return new Date(iso).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function Library() {
  const [params, setParams] = useSearchParams()
  const tab = TABS.some((t) => t.id === params.get('tab')) ? params.get('tab') : 'liked'
  const [ratings, setRatings] = useState(null) // your likes and dislikes
  const [history, setHistory] = useState(null) // every watch, newest first
  const [error, setError] = useState('')
  const [removeError, setRemoveError] = useState('')
  const tabRefs = useRef({})

  const load = useCallback(() => {
    setError('')
    setRatings(null)
    setHistory(null)
    Promise.all([apiFetch('/me/likes'), apiFetch('/me/history')])
      .then(([likes, watches]) => {
        setRatings(likes)
        setHistory(watches)
      })
      .catch((failure) => setError(failure.message))
  }, [])

  useEffect(load, [load])

  function openTab(id) {
    setParams(id === 'liked' ? {} : { tab: id }, { replace: true })
  }

  // Left and Right arrows move between the tabs, as in any tab list.
  function onTabKey(event) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key]
    if (!step) return
    const index = TABS.findIndex((t) => t.id === tab)
    const next = TABS[(index + step + TABS.length) % TABS.length].id
    openTab(next)
    tabRefs.current[next]?.focus()
  }

  async function remove(tmdbId) {
    setRemoveError('')
    try {
      await apiFetch(`/me/likes?tmdb_id=${tmdbId}`, { method: 'DELETE' })
      setRatings((list) => list.filter((film) => film.tmdb_id !== tmdbId))
    } catch (failure) {
      setRemoveError(failure.message)
    }
  }

  const lists = ratings && history && {
    liked: ratings.filter((film) => film.value === 1),
    disliked: ratings.filter((film) => film.value === -1),
    watched: history,
  }
  const films = lists?.[tab]

  return (
    <>
      <h1>Your library</h1>
      <div className="tabs" role="tablist" aria-label="Your films">
        {TABS.map((t) => (
          <button
            key={t.id}
            ref={(element) => {
              tabRefs.current[t.id] = element
            }}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls="library-panel"
            tabIndex={tab === t.id ? 0 : -1}
            className="tab"
            onClick={() => openTab(t.id)}
            onKeyDown={onTabKey}
          >
            {t.label}
            {lists && <span className="tab-count"> {lists[t.id].length}</span>}
          </button>
        ))}
      </div>

      <div id="library-panel" role="tabpanel" aria-labelledby={`tab-${tab}`}>
        {error && <ErrorMessage message={error} onRetry={load} />}
        {!error && !films && <Loading count={6} label="Loading your films" />}
        {removeError && (
          <p className="form-error" role="alert">
            {removeError}
          </p>
        )}
        {films?.length === 0 && (
          <Empty title={EMPTY[tab][0]} action={<Link to="/discover" className="button">Browse films</Link>}>
            {EMPTY[tab][1]}
          </Empty>
        )}
        {films?.length > 0 && (
          <ul className="poster-grid movie-grid">
            {films.map((film) => (
              <li key={tab === 'watched' ? `${film.tmdb_id}-${film.watched_at}` : film.tmdb_id} className="library-item">
                <MovieCard film={film} />
                {tab === 'watched' ? (
                  <span className="library-note">Watched {dateText(film.watched_at)}</span>
                ) : (
                  <button type="button" className="library-remove" onClick={() => remove(film.tmdb_id)}>
                    Remove<span className="visually-hidden"> {film.title}</span>
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}
