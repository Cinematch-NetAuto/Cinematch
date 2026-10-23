// The reason ticket under a recommended film: why it was picked (in Marquee),
// its first two genres, and its rating on a torn-off stub. It has no outline:
// two notches cut from its sides give it the ticket shape (docs/design.md,
// "The reason card").
//
// `film` is a Recommendation from the backend (a MovieCard plus `reason`).
// `genreNames` maps genre id to name. While it is empty, `genres` is empty too,
// so repeatsReason is true and the genre line is left out.
import { ratingOf } from './MovieCard.jsx'

export default function ReasonChip({ film, genreNames }) {
  const rating = ratingOf(film)
  const genres = film.genre_ids.map((id) => genreNames[id]).filter(Boolean).slice(0, 2)
  // "Because you like Drama" over a line that says only "Drama" says it twice.
  const repeatsReason = genres.every((name) => film.reason.includes(name))

  return (
    <p className="reason-ticket">
      <span className="reason-text">
        <span className="reason">{film.reason}</span>
        {!repeatsReason && (
          <span className="reason-genres">
            <span className="visually-hidden">. </span>
            {genres.join(' and ')}
          </span>
        )}
      </span>
      {rating && (
        <span className="reason-stub">
          <span className="visually-hidden">. Rated </span>
          {rating}
          <span className="visually-hidden"> out of 10</span>
        </span>
      )}
    </p>
  )
}
