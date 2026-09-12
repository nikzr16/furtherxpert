import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const justRegistered = location.state?.justRegistered
  const from = location.state?.from?.pathname || '/my-results'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      if (err.status === 429) {
        setError('Too many attempts. Please wait a minute and try again.')
      } else {
        setError('Wrong email or password.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h2 className="text-xl font-semibold">Log in</h2>

      {justRegistered && (
        <p className="mt-3 rounded border border-green-300 bg-green-50 p-2 text-sm text-green-800">
          Account created. Log in to continue.
        </p>
      )}
      {error && (
        <p className="mt-3 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800" role="alert">
          {error}
        </p>
      )}

      <form className="mt-4 space-y-4" onSubmit={handleSubmit} noValidate>
        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-blue-700 px-4 py-2 text-white hover:bg-blue-800 disabled:opacity-50"
        >
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        No account yet?{' '}
        <Link to="/register" className="underline hover:no-underline">
          Register
        </Link>
      </p>
    </main>
  )
}
