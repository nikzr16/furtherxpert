import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPrograms, getUniversities } from '../api'
import { displayProgram } from '../programName'

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

  if (loading) return <p className="mx-auto max-w-4xl p-6 text-gray-500">Loading…</p>
  if (error) return <p className="mx-auto max-w-4xl p-6 text-red-700">{error}</p>

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h2 className="text-xl font-semibold">Explore diploma programs</h2>

      <div className="mt-4 flex flex-wrap gap-3">
        <div>
          <label htmlFor="area-filter" className="block text-sm font-medium">
            Area
          </label>
          <select
            id="area-filter"
            className="mt-1 rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={area}
            onChange={(e) => setArea(e.target.value)}
          >
            <option value="">All areas</option>
            {areas.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="university-filter" className="block text-sm font-medium">
            University
          </label>
          <select
            id="university-filter"
            className="mt-1 rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
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
        <div className="flex-1">
          <label htmlFor="search" className="block text-sm font-medium">
            Search
          </label>
          <input
            id="search"
            type="search"
            placeholder="Program name"
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <p className="mt-3 text-sm text-gray-600" aria-live="polite">
        {filtered.length} program{filtered.length === 1 ? '' : 's'}
      </p>

      <ul className="mt-2 space-y-2">
        {filtered.map((program) => (
          <li key={program.code} className="rounded border border-gray-200 p-3">
            <Link to={`/programs/${program.code}`} className="font-medium underline hover:no-underline">
              {displayProgram(program.name).name}
            </Link>
            <p className="text-sm text-gray-600">
              {program.university_name} · {program.area || 'Uncategorised'}
              {program.avg_merit != null && ` · Average merit ${program.avg_merit}`}
            </p>
            <div className="mt-1 flex flex-wrap gap-1">
              {displayProgram(program.name).isNew && <Badge>New</Badge>}
              {program.stem && <Badge>STEM</Badge>}
              {program.tvet && <Badge>TVET</Badge>}
              {program.bumiputera_only && <Badge>Bumiputera only</Badge>}
              {program.interview && <Badge>Interview required</Badge>}
            </div>
          </li>
        ))}
      </ul>
    </main>
  )
}

function Badge({ children }) {
  return <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">{children}</span>
}
