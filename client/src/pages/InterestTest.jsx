import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getInterestTestQuestions, getMyInterestAnswers, putMyInterestAnswers } from '../api'
import { useAuth } from '../context/AuthContext'

export default function InterestTest() {
  const { authedFetch } = useAuth()
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({}) // question_id -> option_id
  const [savingQuestionId, setSavingQuestionId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [saveError, setSaveError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [questionList, progress] = await Promise.all([
          getInterestTestQuestions(),
          getMyInterestAnswers(authedFetch),
        ])
        if (cancelled) return
        setQuestions(questionList)
        const byQuestion = Object.fromEntries(progress.answers.map((a) => [a.question_id, a.option_id]))
        setAnswers(byQuestion)
      } catch (error) {
        if (!cancelled) setLoadError(error.message || 'Could not load the interest test.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [authedFetch])

  const answeredCount = Object.keys(answers).length
  const complete = questions.length > 0 && answeredCount >= questions.length

  async function choose(questionId, optionId) {
    setSaveError(null)
    setSavingQuestionId(questionId)
    const previous = answers[questionId]
    // Save-as-you-go: a partial PUT merges into what's already saved
    // (decision 0008), so sending just this one answer is enough.
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }))
    try {
      await putMyInterestAnswers(authedFetch, [{ question_id: questionId, option_id: optionId }])
    } catch (error) {
      setSaveError(error.message || 'Could not save that answer. Please try again.')
      setAnswers((prev) => ({ ...prev, [questionId]: previous }))
    } finally {
      setSavingQuestionId(null)
    }
  }

  if (loading) return <p className="mx-auto max-w-2xl p-6 text-gray-500">Loading…</p>
  if (loadError) return <p className="mx-auto max-w-2xl p-6 text-red-700">{loadError}</p>

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h2 className="text-xl font-semibold">Interest test</h2>
      <p className="mt-2 text-gray-600">
        Pick whichever option feels closest. Each answer saves right away, so you can close this and come back later
        -- you'll pick up right where you left off.
      </p>

      <div
        className="mt-3 rounded border border-gray-200 bg-gray-50 p-2 text-sm font-medium"
        role="status"
        aria-live="polite"
      >
        {answeredCount} of {questions.length} answered
      </div>
      {saveError && (
        <p className="mt-2 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800" role="alert">
          {saveError}
        </p>
      )}
      {complete && (
        <p className="mt-2 rounded border border-green-300 bg-green-50 p-2 text-sm text-green-800">
          You've answered every question.{' '}
          <Link to="/my-results" className="underline hover:no-underline">
            View your results
          </Link>
          .
        </p>
      )}

      <ol className="mt-4 space-y-6">
        {questions.map((question, index) => (
          <li key={question.id} className="rounded border border-gray-200 p-4">
            <fieldset>
              <legend className="font-medium">
                {index + 1}. {question.text}
              </legend>
              <div className="mt-2 space-y-1">
                {question.options.map((option) => (
                  <label key={option.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      checked={answers[question.id] === option.id}
                      onChange={() => choose(question.id, option.id)}
                      disabled={savingQuestionId === question.id}
                    />
                    {option.text}
                  </label>
                ))}
              </div>
              {savingQuestionId === question.id && <p className="mt-1 text-xs text-gray-500">Saving…</p>}
            </fieldset>
          </li>
        ))}
      </ol>
    </main>
  )
}
