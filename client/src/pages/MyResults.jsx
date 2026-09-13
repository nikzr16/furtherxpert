import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyAnalysis } from '../api'
import { useAuth } from '../context/AuthContext'
import RadarChartCard from '../components/RadarChartCard'
import EligibilityBadge from '../components/EligibilityBadge'
import AISummaryCard from '../components/AISummaryCard'
import { displayProgram } from '../programName'

export default function MyResults() {
  const { authedFetch } = useAuth()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getMyAnalysis(authedFetch)
      .then((data) => {
        if (!cancelled) setAnalysis(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Could not load your results.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [authedFetch])

  const subjectGroupData = analysis ? analysis.subject_groups.map((g) => ({ name: g.name, score: g.score })) : []
  const interestAreaData =
    analysis && analysis.interest_test_complete
      ? analysis.interest_areas.map((a) => ({ name: a.area, score: a.score }))
      : []

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h2 className="text-xl font-semibold">My results</h2>

      {/* Its own independent fetch (PRD T7 acceptance criterion 7) -- it
          mounts and loads regardless of the charts' own loading/error state
          below, so a slow or failed AI call never blocks the charts. */}
      <AISummaryCard />

      {loading && <p className="mt-4 text-gray-500">Loading…</p>}
      {!loading && error && <p className="mt-4 text-red-700">{error}</p>}

      {!loading && !error && (
        <>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <RadarChartCard
              title="What you're likely to excel in"
              data={subjectGroupData}
              scoreLabel="Percent"
              emptyMessage={
                <>
                  Add your SPM results to see this chart.{' '}
                  <Link to="/results" className="underline hover:no-underline">
                    Add results
                  </Link>
                </>
              }
            />
            <RadarChartCard
              title="What you're likely to love"
              data={interestAreaData}
              scoreLabel="Percent"
              emptyMessage={
                <>
                  Finish the interest test to see this chart.{' '}
                  <Link to="/interest-test" className="underline hover:no-underline">
                    Take the interest test
                  </Link>
                </>
              }
            />
          </div>

          <section className="mt-6">
            <h3 className="text-lg font-semibold">Best fit</h3>
            {analysis.best_fit.length === 0 && (
              <p className="mt-2 text-gray-500">
                Add your SPM results and finish the interest test to see your best-fit programs.
              </p>
            )}
            <div className="mt-2 space-y-4">
              {analysis.best_fit.map((areaEntry) => {
                const isExcel = analysis.likely_to_excel.some((a) => a.area === areaEntry.area)
                const isLove = analysis.likely_to_love.some((a) => a.area === areaEntry.area)
                const isSweetSpot = analysis.sweet_spots.includes(areaEntry.area)
                return (
                  <div key={areaEntry.area} className="rounded border border-gray-200 p-4">
                    <h4 className="flex flex-wrap items-center gap-2 font-semibold">
                      {areaEntry.area}
                      {isSweetSpot && (
                        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800">
                          Sweet spot
                        </span>
                      )}
                      {!isSweetSpot && isExcel && (
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                          Likely to excel
                        </span>
                      )}
                      {!isSweetSpot && isLove && (
                        <span className="rounded-full bg-pink-100 px-2 py-0.5 text-xs font-medium text-pink-800">
                          Likely to love
                        </span>
                      )}
                    </h4>
                    {areaEntry.programs.length === 0 ? (
                      <p className="mt-1 text-sm text-gray-500">No matching eligible programs yet.</p>
                    ) : (
                      <ul className="mt-2 space-y-2">
                        {areaEntry.programs.map((program) => (
                          <li key={program.code} className="border-t border-gray-100 pt-2 first:border-t-0 first:pt-0">
                            <Link to={`/programs/${program.code}`} className="font-medium underline hover:no-underline">
                              {displayProgram(program.name).name}
                            </Link>{' '}
                            <span className="text-sm text-gray-600">({program.university})</span>
                            <EligibilityBadge verdict={program.verdict} reasons={program.reasons} />
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        </>
      )}
    </main>
  )
}
