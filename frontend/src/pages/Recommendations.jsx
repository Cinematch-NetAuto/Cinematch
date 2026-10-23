// Your 20 recommendations, at /me/recommendations: the posters, best first, each
// with a reason ticket that says why it was picked. The picking happens in the
// backend (backend/app/services/recommend.py), so a like or a dislike changes
// this list the next time the page loads.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import MovieCard from '../components/MovieCard.jsx'
import ReasonChip from '../components/ReasonChip.jsx'
import { Empty, ErrorMessage, Loading } from '../components/States.jsx'

export default function Recommendations() {
  const [films, setFilms] = useState(null)
  const [genreNames, setGenreNames] = useState({})
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setFilms(null)
    setError('')
    let current = true
    apiFetch('/me/recommendations')
      .then((answer) => current && setFilms(answer))
      .catch((failure) => current && setError(failure.message))
    return () => {
      current = false
    }
  }, [])

  useEffect(load, [load])

  // Genre names for the tickets. If they fail to load, the tickets still show
  // the reason and the rating.
  useEffect(() => {
    let current = true
    apiFetch('/genres')
      .then((genres) => current && setGenreNames(Object.fromEntries(genres.map((g) => [g.id, g.name]))))
      .catch(() => {})
    return () => {
      current = false
    }
  }, [])

  return (
    <>
      <h1>For you</h1>
      <p className="search-hint">
        We picked these films based on the films you liked and the genres you chose. Like or dislike more films to
        change this list.
      </p>
      {error && <ErrorMessage message={error} onRetry={load} />}
      {!error && !films && <Loading count={12} label="Loading your recommendations" />}
      {films?.length === 0 && (
        <Empty title="No new films to suggest." action={<Link to="/discover" className="button">Browse films</Link>}>
          You have already watched or rated the films we found. Like a few more films, and we will look again.
        </Empty>
      )}
      {films?.length > 0 && (
        <ul className="poster-grid movie-grid">
          {films.map((film) => (
            <li key={film.tmdb_id} className="recommendation">
              <MovieCard film={film} showRating={false} />
              <ReasonChip film={film} genreNames={genreNames} />
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
