import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getProgram } from '../api'
import { displayProgram } from '../programName'

export default function ProgramDetail() {
  const { code } = useParams()
  const [program, setProgram] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  if (loading) return <p className="mx-auto max-w-3xl p-6 text-gray-500">Loading…</p>
  if (error) {
    return (
      <main className="mx-auto max-w-3xl p-6">
        <p className="text-red-700">{error}</p>
        <Link to="/explore" className="mt-2 inline-block underline hover:no-underline">
          Back to Explore
        </Link>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <Link to="/explore" className="text-sm underline hover:no-underline">
        Back to Explore
      </Link>
      <h2 className="mt-2 text-xl font-semibold">{displayProgram(program.name).name}</h2>
      <p className="text-gray-600">
        {program.university_name} ({program.university_code}) · {program.code}
      </p>

      <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <dt className="font-medium">Area</dt>
        <dd>{program.area || 'Uncategorised'}</dd>
        <dt className="font-medium">Level</dt>
        <dd>{program.level || '—'}</dd>
        <dt className="font-medium">Mode</dt>
        <dd>{program.mode || '—'}</dd>
        <dt className="font-medium">Duration</dt>
        <dd>
          {program.duration_value != null ? `${program.duration_value} ${program.duration_unit || ''}` : '—'}
        </dd>
        <dt className="font-medium">Average merit</dt>
        <dd>{program.avg_merit != null ? program.avg_merit : '—'}</dd>
        <dt className="font-medium">Campuses</dt>
        <dd>{program.campuses.length > 0 ? program.campuses.join(', ') : '—'}</dd>
      </dl>

      <div className="mt-3 flex flex-wrap gap-1">
        {program.stem && <Badge>STEM</Badge>}
        {program.tvet && <Badge>TVET</Badge>}
        {program.bumiputera_only && <Badge>Bumiputera only</Badge>}
        {program.interview && <Badge>Interview required</Badge>}
      </div>

      {program.career_paths.length > 0 && (
        <section className="mt-4">
          <h3 className="font-semibold">Career paths</h3>
          <ul className="mt-1 list-inside list-disc text-sm">
            {program.career_paths.map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-4">
        <h3 className="font-semibold">Entry requirements</h3>
        <p className="mt-1 text-sm text-gray-600">
          The original Malay wording from e-Panduan UPU, for both intake categories. {program.source_credit}.
        </p>
        {program.general_requirements.map((req) => (
          <div key={`general-${req.category}`} className="mt-2 rounded border border-gray-200 p-3">
            <h4 className="text-sm font-semibold">General requirements (syarat am) -- Category {req.category}</h4>
            <p className="mt-1 whitespace-pre-wrap text-sm">{req.text_ms}</p>
          </div>
        ))}
        {program.requirements.map((req) => (
          <div key={`program-${req.category}`} className="mt-2 rounded border border-gray-200 p-3">
            <h4 className="text-sm font-semibold">Program requirements (syarat khas) -- Category {req.category}</h4>
            <p className="mt-1 whitespace-pre-wrap text-sm">{req.text_ms}</p>
          </div>
        ))}
      </section>

      <p className="mt-4 text-xs text-gray-500">{program.source_credit}</p>
    </main>
  )
}

function Badge({ children }) {
  return <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">{children}</span>
}
