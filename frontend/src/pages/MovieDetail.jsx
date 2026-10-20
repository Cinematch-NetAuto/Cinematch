// One film's page, at /movie/:id (the TMDB film id): the backdrop, poster,
// facts, overview and cast, and, when you are logged in, Like, Dislike and
// "Mark as watched". The buttons come from the backend, not from memory, so
// after a refresh they still show what you chose.
import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { ratingOf, yearOf } from '../components/MovieCard.jsx'
import { Empty, ErrorMessage } from '../components/States.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function runtimeText(minutes) {
  if (!minutes) return null
  const hours = Math.floor(minutes / 60)
  return hours ? `${hours} h ${minutes % 60} min` : `${minutes} min`
}

function dateText(iso) {
  return new Date(iso).toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })
}

// Like, Dislike and "Mark as watched" for a logged-in user.
function MyChoices({ tmdbId }) {
  const [rating, setRating] = useState(0) // 1 liked, -1 disliked, 0 neither
  const [lastWatched, setLastWatched] = useState(null)
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // What you chose before, so a refresh shows the right state.
  useEffect(() => {
    let current = true
    Promise.all([apiFetch('/me/likes'), apiFetch('/me/history')])
      .then(([likes, history]) => {
        if (!current) return
        setRating(likes.find((film) => film.tmdb_id === tmdbId)?.value ?? 0)
        setLastWatched(history.find((film) => film.tmdb_id === tmdbId)?.watched_at ?? null)
        setReady(true)
      })
      .catch((failure) => current && setError(failure.message))
    return () => {
      current = false
    }
  }, [tmdbId])

  async function act(work) {
    setBusy(true)
    setError('')
    try {
      await work()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setBusy(false)
    }
  }

  // Clicking the chosen button again takes the choice back.
  const rate = (value) =>
    act(async () => {
      if (rating === value) {
        await apiFetch(`/me/likes?tmdb_id=${tmdbId}`, { method: 'DELETE' })
        setRating(0)
      } else {
        await apiFetch('/me/likes', { method: 'PUT', body: { tmdb_id: tmdbId, value } })
        setRating(value)
      }
    })

  const markWatched = () =>
    act(async () => {
      const watch = await apiFetch('/me/history', { method: 'POST', body: { tmdb_id: tmdbId } })
      setLastWatched(watch.watched_at)
    })

  if (!ready && !error) return <p role="status">Loading your choices…</p>

  return (
    <div className="film-actions">
      <div className="tiles">
        <button type="button" className="tile choice-like" aria-pressed={rating === 1} disabled={busy} onClick={() => rate(1)}>
          {rating === 1 ? 'Liked' : 'Like'}
        </button>
        <button type="button" className="tile choice-dislike" aria-pressed={rating === -1} disabled={busy} onClick={() => rate(-1)}>
          {rating === -1 ? 'Disliked' : 'Dislike'}
        </button>
        <button type="button" className="tile" disabled={busy} onClick={markWatched}>
          {lastWatched ? 'Watched it again' : 'Mark as watched'}
        </button>
      </div>
      {lastWatched && <p className="field-hint">You last watched it on {dateText(lastWatched)}.</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default function MovieDetail() {
  const { id } = useParams()
  const tmdbId = Number(id)
  const { user } = useAuth()
  const location = useLocation()
  const [film, setFilm] = useState(null)
  const [failure, setFailure] = useState(null)

  const load = useCallback(() => {
    setFilm(null)
    setFailure(null)
    let current = true
    apiFetch(`/movies/${tmdbId}`)
      .then((answer) => current && setFilm(answer))
      .catch((problem) => current && setFailure(problem))
    return () => {
      current = false
    }
  }, [tmdbId])

  useEffect(load, [load])

  if (failure?.status === 404 || failure?.status === 422) {
    return (
      <Empty title="We could not find that film." action={<Link to="/discover" className="button">Browse films</Link>}>
        The link may be old or mistyped.
      </Empty>
    )
  }
  if (failure) return <ErrorMessage message={failure.message} onRetry={load} />
  if (!film) return <p role="status">Loading the film…</p>

  const rating = ratingOf(film)
  const facts = [yearOf(film), runtimeText(film.runtime), rating && `Rated ${rating} from ${film.vote_count.toLocaleString('en')} votes`].filter(Boolean)

  return (
    <article className="film">
      <header className="film-hero">
        {film.backdrop_url && <img className="film-backdrop" src={film.backdrop_url} alt="" />}
        <div className="film-hero-inner">
          {film.poster_url ? (
            <img className="poster film-poster" src={film.poster_url} alt={`Poster of ${film.title}`} />
          ) : (
            <span className="poster poster-empty film-poster" aria-hidden="true">
              {film.title}
            </span>
          )}
          <div className="film-heading">
            <h1 className="film-title">{film.title}</h1>
            {film.tagline && <p className="film-tagline">{film.tagline}</p>}
            <p className="film-facts">
              {facts.map((fact) => (
                <span key={fact}>{fact} </span>
              ))}
            </p>
            {film.genres.length > 0 && <p className="film-facts">{film.genres.map((g) => g.name).join(', ')}</p>}
          </div>
        </div>
      </header>

      {user ? (
        <MyChoices tmdbId={tmdbId} />
      ) : (
        <p className="film-actions">
          <Link to="/login" state={{ from: location.pathname }}>
            Log in
          </Link>{' '}
          to like, dislike or mark films as watched.
        </p>
      )}

      <section aria-labelledby="overview">
        <h2 id="overview">Overview</h2>
        <p>{film.overview || 'No overview yet.'}</p>
      </section>

      {film.cast.length > 0 && (
        <section aria-labelledby="cast">
          <h2 id="cast">Cast</h2>
          <ul className="cast">
            {film.cast.map((person) => (
              <li key={`${person.name}-${person.character}`}>
                {person.profile_url ? (
                  <img className="cast-photo" src={person.profile_url} alt="" loading="lazy" />
                ) : (
                  <span className="cast-photo" aria-hidden="true" />
                )}
                <span className="cast-name">{person.name}</span>{' '}
                {person.character && <span className="cast-role">{person.character}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}
