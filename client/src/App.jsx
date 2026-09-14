import { useEffect } from 'react'
import { Route, BrowserRouter as Router, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Nav from './components/Nav'
import Footer from './components/Footer'
import Home from './pages/Home'
import Register from './pages/Register'
import Login from './pages/Login'
import SpmResults from './pages/SpmResults'
import InterestTest from './pages/InterestTest'
import MyResults from './pages/MyResults'
import Explore from './pages/Explore'
import ProgramDetail from './pages/ProgramDetail'
import Account from './pages/Account'
import NotFound from './pages/NotFound'

// Start each new page at the top, like a normal multi-page site.
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <ScrollToTop />
        <div className="flex min-h-screen flex-col">
          <Nav />
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/explore" element={<Explore />} />
              <Route path="/programs/:code" element={<ProgramDetail />} />
              <Route
                path="/results"
                element={
                  <ProtectedRoute>
                    <SpmResults />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/interest-test"
                element={
                  <ProtectedRoute>
                    <InterestTest />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/my-results"
                element={
                  <ProtectedRoute>
                    <MyResults />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/account"
                element={
                  <ProtectedRoute>
                    <Account />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </AuthProvider>
    </Router>
  )
}

export default App
