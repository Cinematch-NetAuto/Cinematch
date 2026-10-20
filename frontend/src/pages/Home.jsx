// Home page, at /. Popular films for everyone; when you are logged in, a
// "For you" row of your top recommendations comes first. Posters first: a
// logged-out visitor gets one line of welcome and a Sign up button above them.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import MovieGrid from '../components/MovieGrid.jsx'
import { Empty, ErrorMessage, Loading } from '../components/States.jsx'
import { useAuth } from '../context/AuthContext.jsx'

// One row of films with its own loading, empty and error state.
// `path` answers either a list of films or a page ({ results: [...] }).
function FilmSection({ id, title, path, limit, more, empty }) {
  const [films, setFilms] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setFilms(null)
    setError('')
    let current = true
    apiFetch(path)
      .then((answer) => current && setFilms((Array.isArray(answer) ? answer : answer.results).slice(0, limit)))
      .catch((failure) => current && setError(failure.message))
    return () => {
      current = false
    }
  }, [path, limit])

  useEffect(load, [load])

  return (
    <section className="home-section" aria-labelledby={id}>
      <div className="section-head">
        <h2 id={id}>{title}</h2>
        {more}
      </div>
      {error && <ErrorMessage message={error} onRetry={load} />}
      {!error && !films && <Loading count={limit} />}
      {!error && films?.length === 0 && empty}
      {!error && films?.length > 0 && <MovieGrid films={films} />}
    </section>
  )
}

export default function Home() {
  const { user, checking } = useAuth()

  return (
    <>
      <h1 className="visually-hidden">CineMatch home</h1>

      {!checking && !user && (
        <div className="home-welcome">
          <p>Find a film you will like tonight. Pick the genres you love, and every suggestion comes with a reason.</p>
          <Link to="/register" className="button">
            Sign up
          </Link>
        </div>
      )}

      {user && (
        <FilmSection
          id="for-you"
          title="For you"
          path="/me/recommendations"
          limit={6}
          more={<Link to="/me/recommendations">See all</Link>}
          empty={
            <Empty title="Like a few films and we will learn what you like." action={<Link to="/discover" className="button">Browse films</Link>} />
          }
        />
      )}

      <FilmSection
        id="popular"
        title="Popular now"
        path="/movies/discover?sort=popularity&page=1&per_page=20"
        limit={12}
        more={<Link to="/discover">Browse all</Link>}
        empty={<Empty title="No popular films to show right now." />}
      />
    </>
  )
}
