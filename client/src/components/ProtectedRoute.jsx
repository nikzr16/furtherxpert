import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Wraps a page that needs a login. Waits for the silent-refresh attempt on
// app load to finish before deciding, so a logged-in student isn't bounced
// to /login for a moment on every page reload.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, initializing } = useAuth()
  const location = useLocation()

  if (initializing) {
    return (
      <p className="mx-auto max-w-xl p-6 text-gray-500" role="status">
        Loading…
      </p>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}
