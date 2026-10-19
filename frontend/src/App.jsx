// The app's top component: which page shows at which address.
// Every page sits inside the Layout (nav bar and footer). Step 41 keeps
// logged-out visitors away from the /me/... pages.
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Discover from './pages/Discover.jsx'
import Home from './pages/Home.jsx'
import Library from './pages/Library.jsx'
import Login from './pages/Login.jsx'
import MovieDetail from './pages/MovieDetail.jsx'
import Preferences from './pages/Preferences.jsx'
import Recommendations from './pages/Recommendations.jsx'
import Register from './pages/Register.jsx'
import Search from './pages/Search.jsx'

// Any address that is not one of the nine pages.
function NotFound() {
  return (
    <>
      <h1>Page not found</h1>
      <p>
        That address is not part of CineMatch. <Link to="/">Go to the home page</Link>
      </p>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/search" element={<Search />} />
          <Route path="/discover" element={<Discover />} />
          <Route path="/movie/:id" element={<MovieDetail />} />
          <Route path="/me/recommendations" element={<Recommendations />} />
          <Route path="/me/library" element={<Library />} />
          <Route path="/me/preferences" element={<Preferences />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
