// The three states every screen that loads data must show: loading, empty and
// error. Use them like this:
//
//   if (loading) return <Loading />
//   if (error) return <ErrorMessage message="Couldn't load films." onRetry={load} />
//   if (films.length === 0) return (
//     <Empty title="No films match those filters."
//            action={<button className="button" onClick={clear}>Clear filters</button>}>
//       Try a wider year range or a lower rating.
//     </Empty>
//   )
//
// Words: say what happened and what to do next, in one sentence. No "Oops", no
// error codes, no blame.

// Grey poster-shaped blocks, the same size as real cards, so the page does not
// jump when the films arrive. They do not move: the design has no animation.
export function Loading({ count = 10, label = 'Loading films' }) {
  return (
    <div role="status">
      <span className="visually-hidden">{label}…</span>
      <div className="poster-grid" aria-hidden="true">
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className="poster-block" />
        ))}
      </div>
    </div>
  )
}

// Nothing to show yet: an invitation to act, never an apology.
export function Empty({ title, children, action }) {
  return (
    <div className="state">
      <p className="state-title">{title}</p>
      {children && <p>{children}</p>}
      {action}
    </div>
  )
}

// Something failed: what happened, and a way to try again.
export function ErrorMessage({ message, onRetry }) {
  return (
    <div className="state" role="alert">
      <p className="state-title state-error">{message}</p>
      {onRetry && (
        <button type="button" className="button button-quiet" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
