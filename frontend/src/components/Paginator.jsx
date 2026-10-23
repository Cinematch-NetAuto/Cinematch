// "Page N of M" with Previous and Next, and a 10/20 films-per-page toggle.
// The page that shows the list decides what a page change does (usually: write
// it into the address); this component only draws the controls.
export default function Paginator({ page, totalPages, perPage, onPage, onPerPage }) {
  if (!totalPages) return null
  return (
    <nav className="paginator" aria-label="Pages">
      <button type="button" className="button button-quiet" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span className="paginator-where" aria-live="polite">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        className="button button-quiet"
        disabled={page >= totalPages}
        onClick={() => onPage(page + 1)}
      >
        Next
      </button>
      <span className="paginator-size">
        <span id="per-page-label">Films per page</span>
        <span className="tiles" role="group" aria-labelledby="per-page-label">
          {[10, 20].map((size) => (
            <button key={size} type="button" className="tile" aria-pressed={perPage === size} onClick={() => onPerPage(size)}>
              {size}
            </button>
          ))}
        </span>
      </span>
    </nav>
  )
}
