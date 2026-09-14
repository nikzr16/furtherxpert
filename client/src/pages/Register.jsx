import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerAccount } from '../api'
import { MIN_PASSWORD_LENGTH, RACES } from '../constants'
import AuthShell from '../components/AuthShell'
import { Alert, Icon, Spinner } from '../components/ui'

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

  const inputClass = (field) => `input ${fieldErrors[field] ? 'border-red-400 focus:border-red-500 focus:ring-red-500/15' : ''}`

  return (
    <AuthShell
      title="Create your account"
      subtitle="It only takes a minute. We ask for the least we need."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="link">
            Log in
          </Link>
        </>
      }
    >
      {formError && (
        <Alert tone="error" className="mb-5">
          {formError}
        </Alert>
      )}

      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
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
            className={inputClass('email')}
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
          />
          {fieldErrors.email && <p className="field-error">{fieldErrors.email}</p>}
        </div>

        <div>
          <label htmlFor="password" className="label">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="new-password"
            minLength={MIN_PASSWORD_LENGTH}
            className={inputClass('password')}
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
          />
          {fieldErrors.password ? (
            <p className="field-error">{fieldErrors.password}</p>
          ) : (
            <p className="hint">At least {MIN_PASSWORD_LENGTH} characters.</p>
          )}
        </div>

        <fieldset>
          <legend className="label">Are you a Malaysian citizen?</legend>
          <div className="mt-1.5 grid grid-cols-2 gap-2">
            {[
              ['Yes', true],
              ['No', false],
            ].map(([text, value]) => (
              <label
                key={text}
                className="flex cursor-pointer items-center justify-center rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 has-checked:border-indigo-600 has-checked:bg-indigo-50 has-checked:text-indigo-700 has-focus-visible:ring-4 has-focus-visible:ring-indigo-500/20"
              >
                <input
                  type="radio"
                  name="is_citizen"
                  className="sr-only"
                  checked={form.is_citizen === value}
                  onChange={() => update('is_citizen', value)}
                />
                {text}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid gap-5 sm:grid-cols-[1fr_8rem]">
          <div>
            <label htmlFor="race" className="label">
              Race
            </label>
            <select id="race" className="select" value={form.race} onChange={(e) => update('race', e.target.value)}>
              {RACES.map((race) => (
                <option key={race} value={race}>
                  {race}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="spm_year" className="label">
              SPM year
            </label>
            <input
              id="spm_year"
              type="number"
              required
              min={EARLIEST_SPM_YEAR}
              max={CURRENT_YEAR}
              className={inputClass('spm_year')}
              value={form.spm_year}
              onChange={(e) => update('spm_year', e.target.value)}
            />
          </div>
        </div>
        {fieldErrors.spm_year && <p className="field-error -mt-3">{fieldErrors.spm_year}</p>}

        <p className="-mt-2 flex gap-2 rounded-xl bg-slate-50 px-3 py-2.5 text-xs leading-relaxed text-slate-500">
          <Icon name="lock" className="size-4 shrink-0 text-slate-400" />
          We only ask your race to check which programs are reserved for Bumiputera students (Melayu, Anak Negeri
          Sabah, Anak Negeri Sarawak, or Orang Asli). It's never used for anything else.
        </p>

        <div>
          <label className="flex cursor-pointer items-start gap-3 text-sm leading-relaxed text-slate-600">
            <input
              type="checkbox"
              className="mt-1 size-4 shrink-0 cursor-pointer rounded"
              checked={form.consent}
              onChange={(e) => update('consent', e.target.checked)}
            />
            <span>
              I agree that FurtherXpert can store my SPM results and interest-test answers to show me my charts and
              eligible programs, and my race only to check Bumiputera-only programs.
            </span>
          </label>
          {fieldErrors.consent && <p className="field-error">{fieldErrors.consent}</p>}
        </div>

        <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3">
          {submitting && <Spinner className="size-4" />}
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  )
}
