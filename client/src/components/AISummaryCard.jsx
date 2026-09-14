import { useEffect, useState } from 'react'
import { getMyAnalysisSummary } from '../api'
import { useAuth } from '../context/AuthContext'
import { Icon } from './ui'

// The AI summary (Phase 7, PRD T7): fetched with its own independent
// `GET /me/analysis/summary` call, separate from `GET /me/analysis`'s
// charts data -- so a slow or failed AI call never blocks or delays the
// charts (PRD T7 acceptance criterion 7). This component's `useEffect`
// fires on mount, in parallel with wherever it's rendered, not chained
// after the charts' own fetch.
export default function AISummaryCard() {
  const { authedFetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    getMyAnalysisSummary(authedFetch)
      .then((data) => {
        if (!cancelled) setResult(data)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [authedFetch])

  const isOk = !loading && !failed && result?.status === 'ok'
  const notEnoughData = !loading && !failed && result?.status === 'not_enough_data'
  const unavailable = !loading && (failed || result?.status === 'unavailable')

  return (
    <section
      className="relative overflow-hidden rounded-2xl border border-indigo-100 bg-linear-to-br from-indigo-50 via-white to-violet-50 p-5 shadow-sm sm:p-6"
      aria-label="AI summary"
    >
      <div
        className="pointer-events-none absolute -top-16 -right-16 size-48 rounded-full bg-violet-200/40 blur-3xl"
        aria-hidden="true"
      />
      <div className="relative flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-xl bg-linear-to-br from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-600/30">
          <Icon name="sparkles" className="size-5" />
        </span>
        <div>
          <h2 className="font-semibold text-slate-900">Your summary</h2>
          <p className="text-xs text-slate-500">Written by AI from your charts</p>
        </div>
      </div>

      <div className="relative mt-4">
        {loading && (
          <div className="space-y-2.5" role="status" aria-label="Loading your summary">
            <div className="h-3 w-full animate-pulse rounded-full bg-indigo-100" />
            <div className="h-3 w-11/12 animate-pulse rounded-full bg-indigo-100" />
            <div className="h-3 w-3/4 animate-pulse rounded-full bg-indigo-100" />
          </div>
        )}

        {isOk && <p className="leading-relaxed text-slate-700">{result.summary}</p>}

        {notEnoughData && <p className="text-slate-600">{result.message}</p>}

        {unavailable && <p className="text-slate-500">Summary unavailable right now.</p>}
      </div>
    </section>
  )
}
