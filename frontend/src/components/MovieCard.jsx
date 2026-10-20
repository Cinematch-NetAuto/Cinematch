// One film in a poster grid: the poster, the title, the year and the rating.
// The whole card is one link to the film's page.
//
// `film` is a MovieCard from the backend: { tmdb_id, title, release_date,
// poster_url, vote_average, vote_count, ... }. Films without a poster show a
// dusk panel with the title on it; films with no votes say so instead of "0.0".
import { Link } from 'react-router-dom'

export function yearOf(film) {
  return film.release_date ? film.release_date.slice(0, 4) : '—'
}

export function ratingOf(film) {
  return film.vote_count > 0 ? film.vote_average.toFixed(1) : null
}

export default function MovieCard({ film }) {
  const rating = ratingOf(film)
  return (
    <Link to={`/movie/${film.tmdb_id}`} className="movie-card">
      {film.poster_url ? (
        // alt="" because the title is written right below, inside the same link:
        // a screen reader would otherwise read the title twice.
        <img className="poster" src={film.poster_url} alt="" loading="lazy" />
      ) : (
        // Hidden from screen readers: the title is read once, from below.
        <span className="poster poster-empty" aria-hidden="true">
          {film.title}
        </span>
      )}
      <span className="movie-title" title={film.title}>
        {film.title}
      </span>{' '}
      <span className="movie-meta">
        <span>{yearOf(film)}</span>{' '}
        {rating ? (
          <span>
            <span className="visually-hidden">rated </span>
            {rating}
            <span className="visually-hidden"> out of 10</span>
          </span>
        ) : (
          <span>No rating yet</span>
        )}
      </span>
    </Link>
  )
}
