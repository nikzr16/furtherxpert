import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { deleteMe, getMe } from '../api'
import { useAuth } from '../context/AuthContext'
import { Alert, Icon, PageError, PageHeader, PageLoader, Spinner } from '../components/ui'

export default function Account() {
  const { authedFetch, logout } = useAuth()
  const navigate = useNavigate()
  const [me, setMe] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [understood, setUnderstood] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getMe(authedFetch)
      .then((data) => {
        if (!cancelled) setMe(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Could not load your account.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [authedFetch])

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  async function handleDelete() {
    setDeleteError(null)
    setDeleting(true)
    try {
      await deleteMe(authedFetch)
      navigate('/', { replace: true })
    } catch (err) {
      setDeleteError(err.message || 'Could not delete your account. Please try again.')
      setDeleting(false)
    }
  }

  if (loading) return <PageLoader label="Loading your account…" />
  if (error) return <PageError message={error} />

  const details = [
    { label: 'Email', value: me.email },
    { label: 'Malaysian citizen', value: me.is_citizen ? 'Yes' : 'No' },
    { label: 'Race', value: me.race },
    { label: 'SPM year', value: me.spm_year },
  ]

  return (
    <main>
      <PageHeader eyebrow="Settings" title="Account" description="Your profile details and account controls." />

      <div className="container-page max-w-3xl space-y-6 py-8 lg:py-10">
        <section className="card overflow-hidden" aria-labelledby="profile-heading">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-5 sm:px-6">
            <div className="flex min-w-0 items-center gap-4">
              <span className="grid size-12 shrink-0 place-items-center rounded-full bg-linear-to-br from-indigo-500 to-violet-600 text-lg font-semibold text-white">
                {me.email.charAt(0).toUpperCase()}
              </span>
              <div className="min-w-0">
                <h2 id="profile-heading" className="font-semibold text-slate-900">
                  Profile
                </h2>
                <p className="truncate text-sm text-slate-500">{me.email}</p>
              </div>
            </div>
            <button type="button" onClick={handleLogout} className="btn btn-secondary">
              <Icon name="logout" className="size-4" />
              Log out
            </button>
          </div>

          <dl className="divide-y divide-slate-100">
            {details.map((item) => (
              <div key={item.label} className="grid gap-1 px-5 py-3.5 sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-slate-500">{item.label}</dt>
                <dd className="text-sm text-slate-900 sm:col-span-2">{item.value}</dd>
              </div>
            ))}
          </dl>

          <p className="flex gap-2 border-t border-slate-100 bg-slate-50/60 px-5 py-3 text-xs leading-relaxed text-slate-500 sm:px-6">
            <Icon name="lock" className="size-4 shrink-0 text-slate-400" />
            Your race is only used to check Bumiputera-only programs.
          </p>
        </section>

        <section className="card border-red-200 p-5 sm:p-6" aria-labelledby="delete-heading">
          <div className="flex items-start gap-4">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-red-50 text-red-600">
              <Icon name="trash" className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 id="delete-heading" className="font-semibold text-red-700">
                Delete account
              </h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">
                This permanently removes your account, SPM results, interest-test answers, and computed charts. This
                can't be undone.
              </p>

              {!confirmingDelete && (
                <button
                  type="button"
                  onClick={() => setConfirmingDelete(true)}
                  className="btn btn-danger-outline mt-4"
                >
                  Delete my account
                </button>
              )}

              {confirmingDelete && (
                <div className="mt-4 space-y-4 rounded-xl border border-red-200 bg-red-50/50 p-4">
                  {deleteError && <Alert tone="error">{deleteError}</Alert>}
                  <label className="flex cursor-pointer items-start gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      className="mt-0.5 size-4 shrink-0 cursor-pointer accent-red-600"
                      checked={understood}
                      onChange={(e) => setUnderstood(e.target.checked)}
                    />
                    <span>I understand this permanently deletes all of my data and can't be undone.</span>
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={!understood || deleting}
                      className="btn btn-danger"
                    >
                      {deleting && <Spinner className="size-4" />}
                      {deleting ? 'Deleting…' : 'Yes, permanently delete my account'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setConfirmingDelete(false)
                        setUnderstood(false)
                        setDeleteError(null)
                      }}
                      disabled={deleting}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
