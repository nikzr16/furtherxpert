import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getProgram } from '../api'
import { useAuth } from '../context/AuthContext'
import { displayProgram } from '../programName'
import { Icon, PageError, PageLoader, ProgramFlags } from '../components/ui'

export default function ProgramDetail() {
  const { code } = useParams()
  const { isAuthenticated } = useAuth()
  const [program, setProgram] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [category, setCategory] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getProgram(code)
      .then((data) => {
        if (!cancelled) setProgram(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.status === 404 ? 'Program not found.' : err.message || 'Could not load this program.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [code])

  if (loading) return <PageLoader label="Loading program…" />
  if (error) {
    return (
      <PageError message={error}>
        <Link to="/explore" className="btn btn-secondary">
          <Icon name="arrowLeft" className="size-4" />
          Back to Explore
        </Link>
      </PageError>
    )
  }

  const display = displayProgram(program.name)
  const categories = Array.from(
    new Set([...program.general_requirements, ...program.requirements].map((req) => req.category))
  ).sort()
  const activeCategory = categories.includes(category) ? category : categories[0]
  const generalReq = program.general_requirements.find((req) => req.category === activeCategory)
  const programReq = program.requirements.find((req) => req.category === activeCategory)

  const facts = [
    { label: 'Level', value: program.level || '—', icon: 'academicCap' },
    { label: 'Study mode', value: program.mode || '—', icon: 'document' },
    {
      label: 'Duration',
      value: program.duration_value != null ? `${program.duration_value} ${program.duration_unit || ''}` : '—',
      icon: 'clock',
    },
    { label: 'Average merit', value: program.avg_merit != null ? program.avg_merit : '—', icon: 'chartBar' },
  ]

  return (
    <main>
      <div className="border-b border-slate-200/80 bg-white">
        <div className="container-page py-8 sm:py-10">
          <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-slate-500">
            <Link to="/explore" className="transition hover:text-indigo-600">
              Explore
            </Link>
            <Icon name="chevronRight" className="size-3.5 text-slate-400" />
            <span className="truncate text-slate-700">{program.code}</span>
          </nav>

          <div className="mt-5 flex flex-wrap gap-1.5">
            <span className="inline-flex items-center rounded-full bg-indigo-600 px-2.5 py-0.5 text-xs font-medium text-white">
              {program.area || 'Uncategorised'}
            </span>
            <ProgramFlags program={program} isNew={display.isNew} />
          </div>
          <h1 className="mt-3 max-w-3xl text-2xl leading-tight font-semibold tracking-tight text-slate-900 sm:text-4xl">
            {display.name}
          </h1>
          <p className="mt-3 flex items-center gap-2 text-slate-600">
            <Icon name="building" className="size-5 shrink-0 text-slate-400" />
            {program.university_name} ({program.university_code})
          </p>

          <dl className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {facts.map((fact) => (
              <div key={fact.label} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
                <dt className="flex items-center gap-2 text-xs font-medium text-slate-500">
                  <Icon name={fact.icon} className="size-4 text-slate-400" />
                  {fact.label}
                </dt>
                <dd className="mt-1.5 font-semibold text-slate-900">{fact.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      <div className="container-page grid gap-6 py-8 lg:grid-cols-[1fr_20rem] lg:py-10">
        <section className="card p-5 sm:p-6" aria-labelledby="requirements-heading">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 id="requirements-heading" className="text-lg font-semibold text-slate-900">
                Entry requirements
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                The original Malay wording from e-Panduan UPU, for both intake categories.
              </p>
            </div>
            {categories.length > 1 && (
              <div role="tablist" aria-label="Intake category" className="inline-flex shrink-0 rounded-xl bg-slate-100 p-1">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    role="tab"
                    aria-selected={cat === activeCategory}
                    onClick={() => setCategory(cat)}
                    className={`rounded-lg px-3.5 py-1.5 text-sm font-medium transition ${
                      cat === activeCategory ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Category {cat}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div role="tabpanel" className="mt-6 space-y-4">
            <RequirementBlock
              title="General requirements"
              tag="Syarat am"
              category={activeCategory}
              text={generalReq?.text_ms}
            />
            <RequirementBlock
              title="Program requirements"
              tag="Syarat khas"
              category={activeCategory}
              text={programReq?.text_ms}
            />
          </div>

          <p className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-400">{program.source_credit}</p>
        </section>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="relative overflow-hidden rounded-2xl bg-linear-to-br from-indigo-600 to-violet-700 p-5 text-white shadow-lg shadow-indigo-900/20">
            <Icon name="sparkles" className="size-6 text-indigo-200" />
            <h2 className="mt-3 font-semibold">Do you qualify?</h2>
            <p className="mt-1 text-sm text-indigo-100">
              {isAuthenticated
                ? 'See your eligibility and best-fit programs on your dashboard.'
                : 'Add your SPM results to check your eligibility for programs like this one.'}
            </p>
            <Link
              to={isAuthenticated ? '/my-results' : '/register'}
              className="btn mt-4 w-full bg-white text-indigo-700 hover:bg-indigo-50"
            >
              {isAuthenticated ? 'View my results' : 'Get started'}
              <Icon name="arrowRight" className="size-4" />
            </Link>
          </div>

          <div className="card p-5">
            <h2 className="flex items-center gap-2 font-semibold text-slate-900">
              <Icon name="mapPin" className="size-5 text-slate-400" />
              Campuses
            </h2>
            {program.campuses.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {program.campuses.map((campus) => (
                  <li key={campus} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                    {campus}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-500">—</p>
            )}
          </div>

          {program.career_paths.length > 0 && (
            <div className="card p-5">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900">
                <Icon name="briefcase" className="size-5 text-slate-400" />
                Career paths
              </h2>
              <ul className="mt-3 flex flex-wrap gap-2">
                {program.career_paths.map((path) => (
                  <li
                    key={path}
                    className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-sm text-slate-700"
                  >
                    {path}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

function RequirementBlock({ title, tag, category, text }) {
  return (
    <div className="rounded-xl border border-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-slate-50/70 px-4 py-2.5">
        <h3 className="text-sm font-semibold text-slate-900">
          {title} <span className="font-normal text-slate-500">({tag.toLowerCase()})</span>
        </h3>
        {category && <span className="text-xs font-medium text-slate-500">Category {category}</span>}
      </div>
      {text ? (
        <p className="px-4 py-3.5 text-sm leading-relaxed whitespace-pre-wrap text-slate-700">{text}</p>
      ) : (
        <p className="px-4 py-3.5 text-sm text-slate-400 italic">No extra requirements listed for this category.</p>
      )}
    </div>
  )
}
