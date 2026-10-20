// A grid of poster cards: 2 columns on a phone, 6 on a laptop, no media query.
// Pages show <Loading />, <Empty /> or <ErrorMessage /> (States.jsx) instead
// when there are no films to list.
import MovieCard from './MovieCard.jsx'

export default function MovieGrid({ films }) {
  return (
    <ul className="poster-grid movie-grid">
      {films.map((film) => (
        <li key={film.tmdb_id}>
          <MovieCard film={film} />
        </li>
      ))}
    </ul>
  )
}
