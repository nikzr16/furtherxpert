import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyResults, getSubjects, putMyResults } from '../api'
import { useAuth } from '../context/AuthContext'
import { REQUIRED_SUBJECT_CODES, SPM_GRADES } from '../constants'
import { Alert, Badge, Icon, PageError, PageHeader, PageLoader, Spinner } from '../components/ui'

// `PUT /me/results` is upsert-only (it never deletes a subject the payload
// omits), so this page never offers to remove a saved subject -- there's no
// backend route for that yet (docs/furtherxpert-workflow.md Flow 3).
export default function SpmResults() {
  const { authedFetch } = useAuth()
  const [subjects, setSubjects] = useState([])
  const [rows, setRows] = useState([]) // [{subject_code, grade}]
  const [addSubjectCode, setAddSubjectCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [saveError, setSaveError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [subjectList, existingResults] = await Promise.all([getSubjects(), getMyResults(authedFetch)])
        if (cancelled) return
        setSubjects(subjectList)
        setRows(existingResults.map((r) => ({ subject_code: r.subject_code, grade: r.grade })))
      } catch (error) {
        if (!cancelled) setLoadError(error.message || 'Could not load your results.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [authedFetch])

  const subjectByCode = useMemo(() => Object.fromEntries(subjects.map((s) => [s.code, s])), [subjects])
  const usedCodes = useMemo(() => new Set(rows.map((r) => r.subject_code)), [rows])
  const availableSubjects = useMemo(
    () => subjects.filter((s) => !usedCodes.has(s.code)).sort((a, b) => a.name_ms.localeCompare(b.name_ms)),
    [subjects, usedCodes]
  )
  const missingRequired = REQUIRED_SUBJECT_CODES.filter((code) => !usedCodes.has(code))

  function updateGrade(code, grade) {
    setSaved(false)
    setRows((prev) => prev.map((r) => (r.subject_code === code ? { ...r, grade } : r)))
  }

  function addSubject() {
    if (!addSubjectCode) return
    setSaved(false)
    setRows((prev) => [...prev, { subject_code: addSubjectCode, grade: '' }])
    setAddSubjectCode('')
  }

  const ungradedCount = rows.filter((r) => !r.grade).length
  const canSave = rows.length > 0 && ungradedCount === 0 && missingRequired.length === 0

  async function handleSave() {
    setSaveError(null)
    setSaving(true)
    try {
      const saved = await putMyResults(authedFetch, rows)
      setRows(saved.map((r) => ({ subject_code: r.subject_code, grade: r.grade })))
      setSaved(true)
    } catch (error) {
      setSaveError(error.message || 'Could not save your results.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <PageLoader label="Loading your results…" />
  if (loadError) return <PageError message={loadError} />

  return (
    <main>
      <PageHeader
        eyebrow="Step 1 of 2"
        title="Your SPM results"
        description="Add each subject you sat for and pick the grade you got. We use these to work out what you're likely to excel in."
      />

      <div className="container-page grid gap-6 py-8 lg:grid-cols-[1fr_20rem] lg:py-10">
        <div className="space-y-4">
          {missingRequired.length > 0 && (
            <Alert tone="warning">
              Add {missingRequired.map((code) => subjectByCode[code]?.name_ms || code).join(' and ')} before saving.
            </Alert>
          )}
          {saveError && <Alert tone="error">{saveError}</Alert>}
          {saved && (
            <Alert tone="success" title="Results saved">
              <p className="mt-0.5">
                <Link to="/interest-test" className="font-semibold underline underline-offset-2 hover:no-underline">
                  Take the interest test next
                </Link>{' '}
                or{' '}
                <Link to="/my-results" className="font-semibold underline underline-offset-2 hover:no-underline">
                  view your results
                </Link>
                .
              </p>
            </Alert>
          )}

          <section className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
              <h2 className="font-semibold text-slate-900">Subjects</h2>
              <span className="text-sm text-slate-500">
                {rows.length} subject{rows.length === 1 ? '' : 's'}
              </span>
            </div>

            {rows.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <Icon name="document" className="mx-auto size-8 text-slate-300" />
                <p className="mt-3 text-sm text-slate-500">No subjects yet. Add your first subject below.</p>
              </div>
            ) : (
              <table className="w-full border-collapse text-sm">
                <caption className="sr-only">Your SPM subjects and grades</caption>
                <thead className="bg-slate-50/70">
                  <tr className="text-left text-xs tracking-wide text-slate-500 uppercase">
                    <th scope="col" className="px-5 py-2.5 font-medium sm:px-6">
                      Subject
                    </th>
                    <th scope="col" className="w-36 px-5 py-2.5 font-medium sm:px-6">
                      Grade
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map((row) => {
                    const subject = subjectByCode[row.subject_code]
                    const isRequired = REQUIRED_SUBJECT_CODES.includes(row.subject_code)
                    const subjectName = subject ? subject.name_ms : row.subject_code
                    return (
                      <tr key={row.subject_code} className="transition hover:bg-slate-50/60">
                        <td className="px-5 py-3 sm:px-6">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-slate-800">{subjectName}</span>
                            {isRequired && <Badge tone="indigo">Required</Badge>}
                          </div>
                        </td>
                        <td className="px-5 py-2.5 sm:px-6">
                          <label className="sr-only" htmlFor={`grade-${row.subject_code}`}>
                            Grade for {subjectName}
                          </label>
                          <select
                            id={`grade-${row.subject_code}`}
                            className={`select mt-0 py-2 font-medium ${row.grade ? '' : 'border-amber-300 text-slate-400'}`}
                            value={row.grade}
                            onChange={(e) => updateGrade(row.subject_code, e.target.value)}
                          >
                            <option value="">Choose…</option>
                            {SPM_GRADES.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}

            <div className="border-t border-slate-100 bg-slate-50/60 px-5 py-4 sm:px-6">
              <label htmlFor="add-subject" className="label">
                Add a subject
              </label>
              <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
                <select
                  id="add-subject"
                  className="select mt-0"
                  value={addSubjectCode}
                  onChange={(e) => setAddSubjectCode(e.target.value)}
                >
                  <option value="">Choose a subject…</option>
                  {availableSubjects.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.name_ms}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={addSubject} disabled={!addSubjectCode} className="btn btn-secondary">
                  <Icon name="plus" className="size-4" />
                  Add
                </button>
              </div>
            </div>
          </section>

          <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <p className="text-sm text-slate-500">
              {missingRequired.length > 0
                ? 'Bahasa Melayu and Sejarah are still missing.'
                : ungradedCount > 0
                  ? `Pick a grade for ${ungradedCount} more subject${ungradedCount === 1 ? '' : 's'}.`
                  : rows.length > 0
                    ? 'Everything looks good. Save when ready.'
                    : 'Add your subjects to continue.'}
            </p>
            <button type="button" onClick={handleSave} disabled={!canSave || saving} className="btn btn-primary">
              {saving && <Spinner className="size-4" />}
              {saving ? 'Saving…' : 'Save results'}
            </button>
          </div>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="card p-5">
            <h2 className="flex items-center gap-2 font-semibold text-slate-900">
              <Icon name="info" className="size-5 text-indigo-600" />
              Good to know
            </h2>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-600">
              <li className="flex gap-2.5">
                <Icon name="check" className="mt-0.5 size-4 shrink-0 text-emerald-500" strokeWidth={2.5} />
                Bahasa Melayu and Sejarah are required. Every UPU program needs both.
              </li>
              <li className="flex gap-2.5">
                <Icon name="check" className="mt-0.5 size-4 shrink-0 text-emerald-500" strokeWidth={2.5} />
                Only the 10 real SPM grades are allowed.
              </li>
            </ul>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {SPM_GRADES.map((grade) => (
                <span
                  key={grade}
                  className="grid h-7 min-w-9 place-items-center rounded-lg border border-slate-200 bg-slate-50 px-1.5 text-xs font-semibold text-slate-700"
                >
                  {grade}
                </span>
              ))}
            </div>
          </div>

          <Link
            to="/interest-test"
            className="card group flex items-center gap-4 p-5 transition hover:border-indigo-200 hover:shadow-md"
          >
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-rose-50 text-rose-600">
              <Icon name="heart" className="size-5" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-xs font-medium text-slate-500">Step 2 of 2</span>
              <span className="block font-semibold text-slate-900">Interest test</span>
            </span>
            <Icon
              name="arrowRight"
              className="size-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-indigo-600"
            />
          </Link>
        </aside>
      </div>
    </main>
  )
}
