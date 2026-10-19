// One film's page, at /movie/:id (the TMDB film id). Placeholder: step 48 adds
// the poster, overview, cast, and the like, dislike and watched buttons.
import { useParams } from 'react-router-dom'

export default function MovieDetail() {
  const { id } = useParams()
  return <h1>Film {id}</h1>
}
