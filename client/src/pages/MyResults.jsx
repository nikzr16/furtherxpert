import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyAnalysis } from '../api'
import { useAuth } from '../context/AuthContext'
import RadarChartCard from '../components/RadarChartCard'
import { ReasonList, VerdictPill } from '../components/EligibilityBadge'
import AISummaryCard from '../components/AISummaryCard'
import WhyThisDiploma from '../components/WhyThisDiploma'
import { Alert, Badge, Icon, PageHeader, Spinner } from '../components/ui'
import { displayProgram } from '../programName'
import { SUBJECT_GROUPS } from '../constants'

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

  // The backend only returns groups the student took subjects in (PRD T1).
  // The chart shows all 7, with `score: null` ("N/A") for the rest -- display
  // only, no score is worked out here (decision 0019). With no results at all
  // the list stays empty, so the chart keeps its "add your results" state.
  const subjectGroupData = []
  if (analysis && analysis.subject_groups.length > 0) {
    const scoreByGroup = Object.fromEntries(analysis.subject_groups.map((g) => [g.group, g.score]))
    const knownGroups = new Set(SUBJECT_GROUPS.map((g) => g.code))
    for (const g of SUBJECT_GROUPS) subjectGroupData.push({ name: g.name, score: scoreByGroup[g.code] ?? null })
    for (const g of analysis.subject_groups) {
      if (!knownGroups.has(g.group)) subjectGroupData.push({ name: g.name, score: g.score })
    }
  }
  const interestAreaData =
    analysis && analysis.interest_test_complete
      ? analysis.interest_areas.map((a) => ({ name: a.area, score: a.score }))
      : []

  const hasResults = subjectGroupData.length > 0
  const hasInterests = interestAreaData.length > 0

  return (
    <main>
      <PageHeader
        eyebrow="Dashboard"
        title="Your results"
        description="Your strengths and interests side by side, plus the programs that match both."
        actions={
          <>
            <Link to="/results" className="btn btn-secondary">
              <Icon name="document" className="size-4" />
              Edit SPM results
            </Link>
            <Link to="/interest-test" className="btn btn-secondary">
              <Icon name="heart" className="size-4" />
              Interest test
            </Link>
          </>
        }
      />

      <div className="container-page space-y-8 py-8 lg:py-10">
        {/* Its own independent fetch (PRD T7 acceptance criterion 7) -- it
            mounts and loads regardless of the charts' own loading/error state
            below, so a slow or failed AI call never blocks the charts. */}
        <AISummaryCard />

        {loading && (
          <div className="flex items-center justify-center gap-3 py-16 text-slate-500" role="status">
            <Spinner className="size-5 text-indigo-600" />
            <span className="text-sm font-medium">Loading your charts…</span>
          </div>
        )}
        {!loading && error && <Alert tone="error">{error}</Alert>}

        {!loading && !error && (
          <>
            {(!hasResults || !hasInterests) && (
              <section className="card p-5 sm:p-6" aria-label="Setup progress">
                <h2 className="font-semibold text-slate-900">Finish setting up to see your full picture</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <SetupStep done={hasResults} to="/results" title="Add your SPM results" step={1} />
                  <SetupStep done={hasInterests} to="/interest-test" title="Finish the interest test" step={2} />
                </div>
              </section>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
              <RadarChartCard
                variant="excel"
                title="What you're likely to excel in"
                subtitle="Based on your SPM grades"
                data={subjectGroupData}
                scoreLabel="Percent"
                emptyMessage="Add your SPM results to see this chart."
                emptyAction={{ to: '/results', label: 'Add results' }}
              />
              <RadarChartCard
                variant="love"
                title="What you're likely to love"
                subtitle="Based on your interest test"
                data={interestAreaData}
                scoreLabel="Percent"
                emptyMessage="Finish the interest test to see this chart."
                emptyAction={{ to: '/interest-test', label: 'Take the interest test' }}
              />
            </div>

            <section aria-labelledby="best-fit-heading">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 id="best-fit-heading" className="text-xl font-semibold tracking-tight text-slate-900">
                    Best fit
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Programs you can apply for in the areas you're most likely to excel in and love.
                  </p>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 sm:mt-0">
                  <Badge tone="violet" icon="star">
                    Sweet spot = both
                  </Badge>
                </div>
              </div>

              {analysis.best_fit.length === 0 && (
                <div className="card mt-4 px-6 py-12 text-center">
                  <Icon name="layers" className="mx-auto size-8 text-slate-300" />
                  <p className="mx-auto mt-3 max-w-sm text-sm text-slate-500">
                    Add your SPM results and finish the interest test to see your best-fit programs.
                  </p>
                </div>
              )}

              <div className="mt-4 space-y-4">
                {analysis.best_fit.map((areaEntry) => {
                  const isExcel = analysis.likely_to_excel.some((a) => a.area === areaEntry.area)
                  const isLove = analysis.likely_to_love.some((a) => a.area === areaEntry.area)
                  const isSweetSpot = analysis.sweet_spots.includes(areaEntry.area)
                  return (
                    <article
                      key={areaEntry.area}
                      className={`card overflow-hidden ${isSweetSpot ? 'border-violet-200 ring-1 ring-violet-100' : ''}`}
                    >
                      <header
                        className={`flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4 sm:px-6 ${
                          isSweetSpot ? 'border-violet-100 bg-violet-50/50' : 'border-slate-100'
                        }`}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold text-slate-900">{areaEntry.area}</h3>
                          {isSweetSpot && (
                            <Badge tone="violet" icon="star">
                              Sweet spot
                            </Badge>
                          )}
                          {!isSweetSpot && isExcel && (
                            <Badge tone="indigo" icon="academicCap">
                              Likely to excel
                            </Badge>
                          )}
                          {!isSweetSpot && isLove && (
                            <Badge tone="rose" icon="heart">
                              Likely to love
                            </Badge>
                          )}
                        </div>
                        <span className="text-sm text-slate-500">
                          {areaEntry.programs.length} program{areaEntry.programs.length === 1 ? '' : 's'}
                        </span>
                      </header>

                      {areaEntry.programs.length === 0 ? (
                        <p className="px-5 py-6 text-sm text-slate-500 sm:px-6">No matching eligible programs yet.</p>
                      ) : (
                        <ul className="divide-y divide-slate-100">
                          {areaEntry.programs.map((program) => (
                            <li key={program.code} className="px-5 py-4 transition hover:bg-slate-50/70 sm:px-6">
                              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
                                <div className="min-w-0">
                                  <Link
                                    to={`/programs/${program.code}`}
                                    className="font-medium text-slate-900 transition hover:text-indigo-600"
                                  >
                                    {displayProgram(program.name).name}
                                  </Link>
                                  <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-500">
                                    <Icon name="building" className="size-4 shrink-0" />
                                    {program.university}
                                  </p>
                                </div>
                                <VerdictPill verdict={program.verdict} />
                              </div>
                              <ReasonList reasons={program.reasons} />
                              <WhyThisDiploma why={program.why} />
                            </li>
                          ))}
                        </ul>
                      )}
                    </article>
                  )
                })}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  )
}

function SetupStep({ done, to, title, step }) {
  if (done) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50/60 px-4 py-3">
        <span className="grid size-7 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
          <Icon name="check" className="size-4" strokeWidth={2.5} />
        </span>
        <span className="text-sm font-medium text-emerald-900">{title}</span>
      </div>
    )
  }
  return (
    <Link
      to={to}
      className="group flex items-center gap-3 rounded-xl border border-slate-200 px-4 py-3 transition hover:border-indigo-300 hover:bg-indigo-50/40"
    >
      <span className="grid size-7 shrink-0 place-items-center rounded-full border-2 border-slate-300 text-xs font-semibold text-slate-500">
        {step}
      </span>
      <span className="flex-1 text-sm font-medium text-slate-800">{title}</span>
      <Icon name="arrowRight" className="size-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-indigo-600" />
    </Link>
  )
}
