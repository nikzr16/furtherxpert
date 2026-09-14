import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AuthShell from '../components/AuthShell'
import { Alert, Spinner } from '../components/ui'

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
    <AuthShell
      title="Welcome back"
      subtitle="Log in to see your charts and matching programs."
      footer={
        <>
          No account yet?{' '}
          <Link to="/register" className="link">
            Create one
          </Link>
        </>
      }
    >
      <div className="space-y-3">
        {justRegistered && <Alert tone="success">Account created. Log in to continue.</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
      </div>

      <form className={`space-y-5 ${justRegistered || error ? 'mt-5' : ''}`} onSubmit={handleSubmit} noValidate>
        <div>
          <label htmlFor="email" className="label">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password" className="label">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3">
          {submitting && <Spinner className="size-4" />}
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </AuthShell>
  )
}
