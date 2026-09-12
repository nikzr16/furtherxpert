import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Nav from './components/Nav'
import Home from './pages/Home'
import Register from './pages/Register'
import Login from './pages/Login'
import SpmResults from './pages/SpmResults'
import InterestTest from './pages/InterestTest'
import MyResults from './pages/MyResults'
import Explore from './pages/Explore'
import ProgramDetail from './pages/ProgramDetail'
import Account from './pages/Account'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Nav />
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
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
