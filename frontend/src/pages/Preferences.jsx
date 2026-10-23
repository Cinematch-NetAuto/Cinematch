// Your settings, at /me/preferences: favourite genres, a release period, a
// minimum rating and a country. The recommender reads them on every request,
// so "For you" changes as soon as you save. Films you like are listed in your
// Library, not here.
//
// GET /api/me/preferences loads the settings, and "Save" sends them all back
// with PATCH /api/me/preferences. The choices reuse Discover's lists.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { COUNTRIES, PERIODS, RATINGS, Tile } from '../components/FilterPanel.jsx'
import { ErrorMessage, Loading } from '../components/States.jsx'

const MIN_GENRES = 3 // the same rule as the backend (_three_genres in schemas.py)

// The API's answer -> the form. A saved minimum rating of 0 means "any rating".
function toDraft(saved) {
  return {
    genres: saved.preferred_genres,
    yearFrom: saved.year_from,
    yearTo: saved.year_to,
    minRating: saved.min_vote_average || null,
    region: saved.preferred_region ?? '',
  }
}

export default function Preferences() {
  const [draft, setDraft] = useState(null) // null while loading
  const [genres, setGenres] = useState([])
  const [loadError, setLoadError] = useState('')
  const [problem, setProblem] = useState('')
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setLoadError('')
    Promise.all([apiFetch('/me/preferences'), apiFetch('/genres')])
      .then(([settings, genreList]) => {
        setDraft(toDraft(settings))
        setGenres(genreList)
      })
      .catch((failure) => setLoadError(failure.message))
  }, [])

  useEffect(load, [load])

  if (loadError) return <ErrorMessage message={loadError} onRetry={load} />
  if (!draft) return <Loading />

  // Any change hides the "Saved" note until the next save.
  function change(part) {
    setDraft((current) => ({ ...current, ...part }))
    setSaved(false)
  }

  // Built on the latest draft, so two quick clicks both count.
  function toggleGenre(id) {
    setDraft((current) => ({
      ...current,
      genres: current.genres.includes(id)
        ? current.genres.filter((g) => g !== id)
        : [...current.genres, id],
    }))
    setSaved(false)
  }

  async function handleSave(event) {
    event.preventDefault()
    if (draft.genres.length < MIN_GENRES) {
      setProblem(`Choose at least ${MIN_GENRES} genres.`)
      return
    }
    setProblem('')
    setBusy(true)
    try {
      const answer = await apiFetch('/me/preferences', {
        method: 'PATCH',
        body: {
          preferred_genres: draft.genres,
          year_from: draft.yearFrom,
          year_to: draft.yearTo,
          preferred_region: draft.region || null,
          min_vote_average: draft.minRating ?? 0,
        },
      })
      setDraft(toDraft(answer))
      setSaved(true)
    } catch (failure) {
      setProblem(failure.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Preferences</h1>
      <p>
        These settings shape your recommendations. Films you like are in your{' '}
        <Link to="/me/library">Library</Link>.
      </p>
      <form className="form" onSubmit={handleSave} noValidate>
        <fieldset className="field">
          <legend className="field-label">Favourite genres</legend>
          <p className="field-hint">
            Choose at least {MIN_GENRES}. {draft.genres.length} chosen.
          </p>
          <div className="tiles">
            {genres.map((genre) => (
              <Tile key={genre.id} chosen={draft.genres.includes(genre.id)} onClick={() => toggleGenre(genre.id)}>
                {genre.name}
              </Tile>
            ))}
          </div>
        </fieldset>

        <fieldset className="field">
          <legend className="field-label">Release period</legend>
          <div className="tiles">
            {PERIODS.map((period) => (
              <Tile
                key={period.label}
                chosen={draft.yearFrom === period.yearFrom && draft.yearTo === period.yearTo}
                onClick={() => change({ yearFrom: period.yearFrom, yearTo: period.yearTo })}
              >
                {period.label}
              </Tile>
            ))}
          </div>
        </fieldset>

        <fieldset className="field">
          <legend className="field-label">Minimum rating</legend>
          <p className="field-hint">The average score from TMDB viewers, out of 10.</p>
          <div className="tiles">
            {RATINGS.map((rating) => (
              <Tile
                key={rating.label}
                chosen={draft.minRating === rating.value}
                onClick={() => change({ minRating: rating.value })}
              >
                {rating.label}
              </Tile>
            ))}
          </div>
        </fieldset>

        <label className="field">
          <span className="field-label">Made in</span>
          <select value={draft.region} onChange={(event) => change({ region: event.target.value })}>
            <option value="">Any country</option>
            {COUNTRIES.map(([code, name]) => (
              <option key={code} value={code}>
                {name.replace(/^the /, '').replace(/^./, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
        </label>

        {problem && (
          <p className="form-error" role="alert">
            {problem}
          </p>
        )}
        {saved && (
          <p role="status">
            Saved. <Link to="/me/recommendations">See your recommendations</Link>.
          </p>
        )}
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Saving…' : 'Save'}
        </button>
      </form>
    </section>
  )
}
