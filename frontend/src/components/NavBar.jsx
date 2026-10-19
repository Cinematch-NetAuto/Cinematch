// The bar at the top of every page: the CineMatch name (back to Home) and links
// to the other pages. The link to the page you are on is gold.
//
// A film's page has no link here: you reach it from a poster (step 43).
// Step 41 swaps "Log in" and "Sign up" for "Log out" once you are logged in.
import { Link, NavLink } from 'react-router-dom'

const BROWSE = [
  { to: '/search', label: 'Search' },
  { to: '/discover', label: 'Discover' },
  { to: '/me/recommendations', label: 'For you' },
  { to: '/me/library', label: 'Library' },
]

const ACCOUNT = [
  { to: '/me/preferences', label: 'Preferences' },
  { to: '/login', label: 'Log in' },
  { to: '/register', label: 'Sign up' },
]

function Links({ items, className }) {
  return (
    <ul className={className}>
      {items.map(({ to, label }) => (
        <li key={to}>
          {/* NavLink adds class "active" and aria-current="page" on the current page */}
          <NavLink to={to} className="nav-link">
            {label}
          </NavLink>
        </li>
      ))}
    </ul>
  )
}

export default function NavBar() {
  return (
    <header className="nav">
      <nav className="nav-inner" aria-label="Main">
        <Link to="/" className="nav-name">
          CineMatch
        </Link>
        <Links items={BROWSE} className="nav-links" />
        <Links items={ACCOUNT} className="nav-links nav-account" />
      </nav>
    </header>
  )
}
