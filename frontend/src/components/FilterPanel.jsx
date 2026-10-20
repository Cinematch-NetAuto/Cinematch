// The film picker for Discover: genre tiles, a release period, a minimum
// rating, and (folded away) the country and the sort order.
//
// The chosen filters live in the address, with the backend's own names:
//   /discover?genres=878,18&year_from=1990&year_to=1999&min_rating=7&sort=rating
// so a refresh, the Back button or a shared link shows the same films. Clicking
// tiles only changes a draft; "Show films" writes it into the address.
//
// Discover reads the address with readFilters() and asks the backend with
// discoverQuery().
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const DECADES = [1970, 1980, 1990, 2000, 2010, 2020]

export const PERIODS = [
  { label: 'Any time', yearFrom: null, yearTo: null, words: '' },
  { label: 'Before 1970', yearFrom: null, yearTo: 1969, words: 'from before 1970' },
  ...DECADES.map((start) => ({
    label: `${start}s`,
    yearFrom: start,
    yearTo: start + 9,
    words: `from the ${start}s`,
  })),
]

export const RATINGS = [
  { label: 'Any', value: null },
  { label: '6+', value: 6 },
  { label: '7+', value: 7 },
  { label: '8+', value: 8 },
]

export const SORTS = [
  { value: 'popularity', label: 'Most popular', words: 'most popular first' },
  { value: 'rating', label: 'Highest rated', words: 'highest rated first' },
  { value: 'newest', label: 'Newest', words: 'newest first' },
]

// Countries of origin: TMDB's two-letter codes.
export const COUNTRIES = [
  ['US', 'the United States'],
  ['GB', 'the United Kingdom'],
  ['FR', 'France'],
  ['DE', 'Germany'],
  ['IT', 'Italy'],
  ['ES', 'Spain'],
  ['JP', 'Japan'],
  ['KR', 'South Korea'],
  ['CN', 'China'],
  ['IN', 'India'],
  ['AU', 'Australia'],
  ['CA', 'Canada'],
  ['MX', 'Mexico'],
  ['BR', 'Brazil'],
]

const NO_FILTERS = { genres: [], yearFrom: null, yearTo: null, minRating: null, region: '', sort: 'popularity' }

function numberOrNull(value) {
  const number = Number(value)
  return value && Number.isFinite(number) ? number : null
}

// Address -> filters. Anything missing or broken in the address means "any".
export function readFilters(params) {
  const sort = params.get('sort')
  const region = params.get('region') ?? ''
  return {
    genres: (params.get('genres') ?? '').split(',').map(numberOrNull).filter(Boolean),
    yearFrom: numberOrNull(params.get('year_from')),
    yearTo: numberOrNull(params.get('year_to')),
    minRating: numberOrNull(params.get('min_rating')),
    region: /^[A-Z]{2}$/.test(region) ? region : '',
    sort: SORTS.some((s) => s.value === sort) ? sort : 'popularity',
  }
}

// Filters -> the address part (or the backend query): only what is set.
export function filterParams(filters) {
  const out = new URLSearchParams()
  if (filters.genres.length) out.set('genres', filters.genres.join(','))
  if (filters.yearFrom) out.set('year_from', filters.yearFrom)
  if (filters.yearTo) out.set('year_to', filters.yearTo)
  if (filters.minRating) out.set('min_rating', filters.minRating)
  if (filters.region) out.set('region', filters.region)
  if (filters.sort !== 'popularity') out.set('sort', filters.sort)
  return out
}

export function discoverQuery(filters, page, perPage) {
  const query = filterParams(filters)
  query.set('page', page)
  query.set('per_page', perPage)
  return `/movies/discover?${query}`
}

// "Showing sci-fi or drama films from the 1990s, rated 7 or higher."
export function describe(filters, genres) {
  const names = filters.genres
    .map((id) => genres.find((g) => g.id === id)?.name.toLowerCase())
    .filter(Boolean)
  const period = PERIODS.find((p) => p.yearFrom === filters.yearFrom && p.yearTo === filters.yearTo)
  const country = COUNTRIES.find(([code]) => code === filters.region)
  const parts = [`Showing ${names.length ? `${names.join(' or ')} films` : 'films of any genre'}`]
  if (period?.words) parts[0] += ` ${period.words}`
  if (filters.minRating) parts.push(`rated ${filters.minRating} or higher`)
  if (country) parts.push(`made in ${country[1]}`)
  parts.push(SORTS.find((s) => s.value === filters.sort).words)
  return `${parts.join(', ')}.`
}

function Tile({ chosen, onClick, children }) {
  return (
    <button type="button" className="tile" aria-pressed={chosen} onClick={onClick}>
      {children}
    </button>
  )
}

export default function FilterPanel() {
  const [params, setParams] = useSearchParams()
  const applied = useMemo(() => readFilters(params), [params])
  const [draft, setDraft] = useState(applied)
  const [genres, setGenres] = useState([])

  // The address changed (Show films, Back button, a link): start from it again.
  useEffect(() => setDraft(applied), [applied])

  useEffect(() => {
    apiFetch('/genres')
      .then(setGenres)
      .catch(() => setGenres([])) // the picker still works without genre tiles
  }, [])

  const change = (part) => setDraft((current) => ({ ...current, ...part }))

  // Built on the latest draft, so two quick clicks both count.
  function toggleGenre(id) {
    setDraft((current) => ({
      ...current,
      genres: current.genres.includes(id)
        ? current.genres.filter((g) => g !== id)
        : [...current.genres, id],
    }))
  }

  // New filters start again on page 1; the chosen page size is kept.
  function writeAddress(filters) {
    const next = filterParams(filters)
    if (params.get('per_page')) next.set('per_page', params.get('per_page'))
    setParams(next)
  }

  function showFilms(event) {
    event.preventDefault()
    writeAddress(draft)
  }

  return (
    <form className="filter-panel" onSubmit={showFilms}>
      <fieldset className="field">
        <legend className="field-label">Genres</legend>
        <p className="field-hint">Choose any number. Films match at least one.</p>
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
            <Tile key={rating.label} chosen={draft.minRating === rating.value} onClick={() => change({ minRating: rating.value })}>
              {rating.label}
            </Tile>
          ))}
        </div>
      </fieldset>

      <details className="more-filters" open={Boolean(applied.region || applied.sort !== 'popularity')}>
        <summary>More filters</summary>
        <div className="more-filters-body">
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
          <fieldset className="field">
            <legend className="field-label">Sort by</legend>
            <div className="tiles">
              {SORTS.map((sort) => (
                <Tile key={sort.value} chosen={draft.sort === sort.value} onClick={() => change({ sort: sort.value })}>
                  {sort.label}
                </Tile>
              ))}
            </div>
          </fieldset>
        </div>
      </details>

      <div className="filter-actions">
        <p className="filter-summary">{describe(draft, genres)}</p>
        <button type="submit" className="button">
          Show films
        </button>
        <button type="button" className="button button-quiet" onClick={() => writeAddress(NO_FILTERS)}>
          Clear filters
        </button>
      </div>
    </form>
  )
}
