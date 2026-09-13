import { useEffect, useState } from 'react'
import { getMyAnalysisSummary } from '../api'
import { useAuth } from '../context/AuthContext'

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

  return (
    <section className="mt-4 rounded border border-gray-200 p-4" aria-label="AI summary">
      <h3 className="text-lg font-semibold">Your summary</h3>

      {loading && <p className="mt-2 text-gray-500">Loading your summary…</p>}

      {!loading && failed && <p className="mt-2 text-gray-500">Summary unavailable right now.</p>}

      {!loading && !failed && result?.status === 'ok' && <p className="mt-2">{result.summary}</p>}

      {!loading && !failed && result?.status === 'not_enough_data' && (
        <p className="mt-2 text-gray-500">{result.message}</p>
      )}

      {!loading && !failed && result?.status === 'unavailable' && (
        <p className="mt-2 text-gray-500">Summary unavailable right now.</p>
      )}
    </section>
  )
}
