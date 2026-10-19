// The frame around every page: the nav bar, the page itself, and the footer.
// App.jsx puts every route inside this layout; <Outlet /> is where the current
// page appears.
import { Outlet } from 'react-router-dom'
import NavBar from './NavBar.jsx'

export default function Layout() {
  return (
    <div className="page">
      {/* Keyboard users can jump straight past the nav bar. */}
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <NavBar />
      <main id="main" className="page-main">
        <Outlet />
      </main>
      <footer className="page-footer">
        {/* A condition of using the TMDB API. Never remove it. */}
        <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
        <p>
          Film data and images from <a href="https://www.themoviedb.org">TMDB</a>.
        </p>
      </footer>
    </div>
  )
}
