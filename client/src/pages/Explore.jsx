import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPrograms, getUniversities } from '../api'
import { displayProgram } from '../programName'
import { Icon, PageError, PageHeader, PageLoader, ProgramFlags } from '../components/ui'

export default function Explore() {
  const [programs, setPrograms] = useState([])
  const [universities, setUniversities] = useState([])
  const [area, setArea] = useState('')
  const [university, setUniversity] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([getPrograms(), getUniversities()])
      .then(([programList, universityList]) => {
        if (cancelled) return
        setPrograms(programList)
        setUniversities(universityList)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Could not load programs.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const areas = useMemo(
    () => Array.from(new Set(programs.map((p) => p.area).filter(Boolean))).sort(),
    [programs]
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return programs.filter((p) => {
      if (area && p.area !== area) return false
      if (university && p.university_code !== university) return false
      if (q && !p.name.toLowerCase().includes(q)) return false
      return true
    })
  }, [programs, area, university, search])

  const hasFilters = Boolean(area || university || search)

  function clearFilters() {
    setArea('')
    setUniversity('')
    setSearch('')
  }

  if (loading) return <PageLoader label="Loading programs…" />
  if (error) return <PageError message={error} />

  return (
    <main>
      <PageHeader
        eyebrow="Explore"
        title="Diploma programs"
        description="Browse every UPU diploma program at Malaysia's public universities. Filter by area or university, or search by name."
      >
        <div className="mt-8 grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-3 md:grid-cols-[1.4fr_1fr_1fr]">
          <div className="relative">
            <label htmlFor="search" className="sr-only">
              Search
            </label>
            <Icon
              name="search"
              className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-slate-400"
            />
            <input
              id="search"
              type="search"
              placeholder="Search by program name"
              className="input mt-0 pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="area-filter" className="sr-only">
              Area
            </label>
            <select id="area-filter" className="select mt-0" value={area} onChange={(e) => setArea(e.target.value)}>
              <option value="">All areas</option>
              {areas.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="university-filter" className="sr-only">
              University
            </label>
            <select
              id="university-filter"
              className="select mt-0"
              value={university}
              onChange={(e) => setUniversity(e.target.value)}
            >
              <option value="">All universities</option>
              {universities.map((u) => (
                <option key={u.code} value={u.code}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </PageHeader>

      <div className="container-page py-8 lg:py-10">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm text-slate-500" aria-live="polite">
            Showing <span className="font-semibold text-slate-900">{filtered.length}</span> program
            {filtered.length === 1 ? '' : 's'}
          </p>
          {hasFilters && (
            <button type="button" onClick={clearFilters} className="btn btn-ghost btn-sm">
              <Icon name="close" className="size-3.5" />
              Clear filters
            </button>
          )}
        </div>

        {filtered.length === 0 ? (
          <div className="card mt-4 px-6 py-16 text-center">
            <Icon name="search" className="mx-auto size-8 text-slate-300" />
            <p className="mt-3 font-medium text-slate-900">No programs match those filters</p>
            <p className="mt-1 text-sm text-slate-500">Try a different name, or clear the filters.</p>
            <button type="button" onClick={clearFilters} className="btn btn-secondary mt-5">
              Clear filters
            </button>
          </div>
        ) : (
          <ul className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((program) => {
              const display = displayProgram(program.name)
              return (
                <li key={program.code}>
                  <Link
                    to={`/programs/${program.code}`}
                    className="card group flex h-full flex-col p-5 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-lg hover:shadow-indigo-900/5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="truncate text-xs font-semibold text-indigo-600">
                        {program.area || 'Uncategorised'}
                      </span>
                      <Icon
                        name="arrowRight"
                        className="size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600"
                      />
                    </div>
                    <h2 className="mt-2 leading-snug font-semibold text-slate-900 transition group-hover:text-indigo-700">
                      {display.name}
                    </h2>
                    <p className="mt-1.5 flex items-start gap-1.5 text-sm text-slate-500">
                      <Icon name="building" className="mt-0.5 size-4 shrink-0" />
                      {program.university_name}
                    </p>
                    <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-4">
                      <ProgramFlags program={program} isNew={display.isNew} />
                      {program.avg_merit != null && (
                        <span className="ml-auto pl-2 text-xs text-slate-500">
                          Avg. merit <span className="font-semibold text-slate-900 tabular-nums">{program.avg_merit}</span>
                        </span>
                      )}
                    </div>
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </main>
  )
}
