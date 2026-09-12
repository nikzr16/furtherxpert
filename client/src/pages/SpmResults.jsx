import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyResults, getSubjects, putMyResults } from '../api'
import { useAuth } from '../context/AuthContext'
import { REQUIRED_SUBJECT_CODES, SPM_GRADES } from '../constants'

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

  const canSave = rows.length > 0 && rows.every((r) => r.grade) && missingRequired.length === 0

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

  if (loading) return <p className="mx-auto max-w-xl p-6 text-gray-500">Loading…</p>
  if (loadError) return <p className="mx-auto max-w-xl p-6 text-red-700">{loadError}</p>

  return (
    <main className="mx-auto max-w-xl p-6">
      <h2 className="text-xl font-semibold">Your SPM results</h2>
      <p className="mt-2 text-gray-600">
        Bahasa Melayu and Sejarah are required -- every UPU program needs both. Only the 10 real SPM grades are
        allowed.
      </p>

      {missingRequired.length > 0 && (
        <p className="mt-3 rounded border border-yellow-300 bg-yellow-50 p-2 text-sm text-yellow-800">
          Add {missingRequired.map((code) => subjectByCode[code]?.name_ms || code).join(' and ')} before saving.
        </p>
      )}
      {saveError && (
        <p className="mt-3 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800" role="alert">
          {saveError}
        </p>
      )}
      {saved && (
        <p className="mt-3 rounded border border-green-300 bg-green-50 p-2 text-sm text-green-800">
          Saved. <Link to="/interest-test" className="underline hover:no-underline">Take the interest test next</Link>{' '}
          or <Link to="/my-results" className="underline hover:no-underline">view your results</Link>.
        </p>
      )}

      <table className="mt-4 w-full border-collapse text-sm">
        <caption className="sr-only">Your SPM subjects and grades</caption>
        <thead>
          <tr className="border-b border-gray-300 text-left">
            <th scope="col" className="py-1 pr-4">
              Subject
            </th>
            <th scope="col" className="py-1">
              Grade
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const subject = subjectByCode[row.subject_code]
            const isRequired = REQUIRED_SUBJECT_CODES.includes(row.subject_code)
            return (
              <tr key={row.subject_code} className="border-b border-gray-100">
                <td className="py-1 pr-4">
                  {subject ? subject.name_ms : row.subject_code}
                  {isRequired && <span className="text-red-700"> *</span>}
                </td>
                <td className="py-1">
                  <label className="sr-only" htmlFor={`grade-${row.subject_code}`}>
                    Grade for {subject ? subject.name_ms : row.subject_code}
                  </label>
                  <select
                    id={`grade-${row.subject_code}`}
                    className="rounded border border-gray-300 p-1 focus:outline focus:outline-2 focus:outline-blue-600"
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

      <div className="mt-4 flex flex-wrap items-end gap-2">
        <div>
          <label htmlFor="add-subject" className="block text-sm font-medium">
            Add a subject
          </label>
          <select
            id="add-subject"
            className="mt-1 rounded border border-gray-300 p-2 focus:outline focus:outline-2 focus:outline-blue-600"
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
        </div>
        <button
          type="button"
          onClick={addSubject}
          disabled={!addSubjectCode}
          className="rounded border border-gray-300 px-3 py-2 hover:bg-gray-100 disabled:opacity-50"
        >
          Add
        </button>
      </div>

      <button
        type="button"
        onClick={handleSave}
        disabled={!canSave || saving}
        className="mt-6 w-full rounded bg-blue-700 px-4 py-2 text-white hover:bg-blue-800 disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save results'}
      </button>
    </main>
  )
}
