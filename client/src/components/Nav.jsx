import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const linkClass = ({ isActive }) =>
  `rounded px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-600 ${
    isActive ? 'bg-blue-100 text-blue-800' : 'text-gray-700 hover:bg-gray-100'
  }`

export default function Nav() {
  const { isAuthenticated, initializing } = useAuth()

  return (
    <header className="border-b border-gray-200">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-2 p-4">
        <NavLink to="/" className="text-2xl font-bold text-gray-900">
          FurtherXpert
        </NavLink>
        <nav aria-label="Main" className="flex flex-wrap gap-1">
          <NavLink to="/explore" className={linkClass}>
            Explore
          </NavLink>
          {!initializing && !isAuthenticated && (
            <>
              <NavLink to="/login" className={linkClass}>
                Log in
              </NavLink>
              <NavLink to="/register" className={linkClass}>
                Register
              </NavLink>
            </>
          )}
          {!initializing && isAuthenticated && (
            <>
              <NavLink to="/results" className={linkClass}>
                SPM Results
              </NavLink>
              <NavLink to="/interest-test" className={linkClass}>
                Interest Test
              </NavLink>
              <NavLink to="/my-results" className={linkClass}>
                My Results
              </NavLink>
              <NavLink to="/account" className={linkClass}>
                Account
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
