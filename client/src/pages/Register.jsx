import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerAccount } from '../api'
import { MIN_PASSWORD_LENGTH, RACES } from '../constants'

const CURRENT_YEAR = new Date().getFullYear()
const EARLIEST_SPM_YEAR = 1970

const initialForm = {
  email: '',
  password: '',
  is_citizen: true,
  race: RACES[0],
  spm_year: CURRENT_YEAR,
  consent: false,
}

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function validate() {
    const errors = {}
    if (!form.email) errors.email = 'Email is required.'
    if (form.password.length < MIN_PASSWORD_LENGTH) {
      errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`
    }
    const year = Number(form.spm_year)
    if (!Number.isInteger(year) || year < EARLIEST_SPM_YEAR || year > CURRENT_YEAR) {
      errors.spm_year = `SPM year must be between ${EARLIEST_SPM_YEAR} and ${CURRENT_YEAR}.`
    }
    if (!form.consent) errors.consent = 'You must agree before we can create your account.'
    return errors
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError(null)
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitting(true)
    try {
      await registerAccount({ ...form, spm_year: Number(form.spm_year) })
      navigate('/login', { replace: true, state: { justRegistered: true } })
    } catch (error) {
      if (error.status === 409) {
        setFormError('That email is already registered. Log in instead.')
      } else if (error.status === 422) {
        setFormError('Please check the highlighted fields and try again.')
      } else {
        setFormError(error.message || 'Something went wrong. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h2 className="text-xl font-semibold">Create your account</h2>

      {formError && (
        <p className="mt-3 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800" role="alert">
          {formError}
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
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
          />
          {fieldErrors.email && <p className="mt-1 text-sm text-red-700">{fieldErrors.email}</p>}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="new-password"
            minLength={MIN_PASSWORD_LENGTH}
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
          />
          {fieldErrors.password && <p className="mt-1 text-sm text-red-700">{fieldErrors.password}</p>}
        </div>

        <fieldset>
          <legend className="block text-sm font-medium">Are you a Malaysian citizen?</legend>
          <div className="mt-1 flex gap-4">
            <label className="flex items-center gap-1">
              <input
                type="radio"
                name="is_citizen"
                checked={form.is_citizen === true}
                onChange={() => update('is_citizen', true)}
              />
              Yes
            </label>
            <label className="flex items-center gap-1">
              <input
                type="radio"
                name="is_citizen"
                checked={form.is_citizen === false}
                onChange={() => update('is_citizen', false)}
              />
              No
            </label>
          </div>
        </fieldset>

        <div>
          <label htmlFor="race" className="block text-sm font-medium">
            Race
          </label>
          <p className="mt-1 text-sm text-gray-600">
            We only ask this to check which programs are reserved for Bumiputera students (Melayu, Anak Negeri Sabah,
            Anak Negeri Sarawak, or Orang Asli). It's never used for anything else.
          </p>
          <select
            id="race"
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={form.race}
            onChange={(e) => update('race', e.target.value)}
          >
            {RACES.map((race) => (
              <option key={race} value={race}>
                {race}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="spm_year" className="block text-sm font-medium">
            SPM year
          </label>
          <input
            id="spm_year"
            type="number"
            required
            min={EARLIEST_SPM_YEAR}
            max={CURRENT_YEAR}
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={form.spm_year}
            onChange={(e) => update('spm_year', e.target.value)}
          />
          {fieldErrors.spm_year && <p className="mt-1 text-sm text-red-700">{fieldErrors.spm_year}</p>}
        </div>

        <div>
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={form.consent}
              onChange={(e) => update('consent', e.target.checked)}
            />
            <span>
              I agree that FurtherXpert can store my SPM results and interest-test answers to show me my charts and
              eligible programs, and my race only to check Bumiputera-only programs.
            </span>
          </label>
          {fieldErrors.consent && <p className="mt-1 text-sm text-red-700">{fieldErrors.consent}</p>}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-blue-700 px-4 py-2 text-white hover:bg-blue-800 disabled:opacity-50"
        >
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="underline hover:no-underline">
          Log in
        </Link>
      </p>
    </main>
  )
}
