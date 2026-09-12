import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { deleteMe, getMe } from '../api'
import { useAuth } from '../context/AuthContext'

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

  if (loading) return <p className="mx-auto max-w-md p-6 text-gray-500">Loading…</p>
  if (error) return <p className="mx-auto max-w-md p-6 text-red-700">{error}</p>

  return (
    <main className="mx-auto max-w-md p-6">
      <h2 className="text-xl font-semibold">Account</h2>

      <dl className="mt-4 space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="font-medium">Email</dt>
          <dd>{me.email}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium">Citizen</dt>
          <dd>{me.is_citizen ? 'Yes' : 'No'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium">Race</dt>
          <dd>{me.race}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium">SPM year</dt>
          <dd>{me.spm_year}</dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={handleLogout}
        className="mt-6 w-full rounded border border-gray-300 px-4 py-2 hover:bg-gray-100"
      >
        Log out
      </button>

      <div className="mt-8 rounded border border-red-200 p-4">
        <h3 className="font-semibold text-red-800">Delete account</h3>
        <p className="mt-1 text-sm text-gray-600">
          This permanently removes your account, SPM results, interest-test answers, and computed charts. This can't
          be undone.
        </p>

        {!confirmingDelete && (
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="mt-3 rounded border border-red-600 px-4 py-2 text-red-700 hover:bg-red-50"
          >
            Delete my account
          </button>
        )}

        {confirmingDelete && (
          <div className="mt-3 space-y-3">
            {deleteError && (
              <p className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800" role="alert">
                {deleteError}
              </p>
            )}
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5" checked={understood} onChange={(e) => setUnderstood(e.target.checked)} />
              <span>I understand this permanently deletes all of my data and can't be undone.</span>
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleDelete}
                disabled={!understood || deleting}
                className="rounded bg-red-700 px-4 py-2 text-white hover:bg-red-800 disabled:opacity-50"
              >
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
                className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
