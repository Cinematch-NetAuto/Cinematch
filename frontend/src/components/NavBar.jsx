// The bar at the top of every page: the CineMatch name (back to Home) and links
// to the other pages. The link to the page you are on is gold.
//
// A film's page has no link here: you reach it from a poster (step 43).
// Logged out: "Log in" and "Sign up". Logged in: your name, "Preferences" and
// "Log out".
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

const BROWSE = [
  { to: '/search', label: 'Search' },
  { to: '/discover', label: 'Discover' },
  { to: '/me/recommendations', label: 'For you' },
  { to: '/me/library', label: 'Library' },
]

function NavItem({ to, label }) {
  return (
    <li>
      {/* NavLink adds class "active" and aria-current="page" on the current page */}
      <NavLink to={to} className="nav-link">
        {label}
      </NavLink>
    </li>
  )
}

export default function NavBar() {
  const { user, logout } = useAuth()

  // A full reload at Home. A router move would lose the race: the /me/... page
  // you are on would see "logged out" first and send you to /login instead.
  // The reload also clears anything of yours still held in the page.
  function handleLogout() {
    logout()
    window.location.assign('/')
  }

  return (
    <header className="nav">
      <nav className="nav-inner" aria-label="Main">
        <Link to="/" className="nav-name">
          CineMatch
        </Link>
        <ul className="nav-links">
          {BROWSE.map((item) => (
            <NavItem key={item.to} {...item} />
          ))}
        </ul>
        <ul className="nav-links nav-account">
          {user ? (
            <>
              <li className="nav-user">{user.display_name}</li>
              <NavItem to="/me/preferences" label="Preferences" />
              <li>
                <button type="button" className="nav-link nav-button" onClick={handleLogout}>
                  Log out
                </button>
              </li>
            </>
          ) : (
            <>
              <NavItem to="/login" label="Log in" />
              <NavItem to="/register" label="Sign up" />
            </>
          )}
        </ul>
      </nav>
    </header>
  )
}
