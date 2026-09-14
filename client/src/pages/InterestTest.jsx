import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getInterestTestQuestions, getMyInterestAnswers, putMyInterestAnswers } from '../api'
import { useAuth } from '../context/AuthContext'
import { Alert, Icon, PageError, PageHeader, PageLoader, Spinner } from '../components/ui'

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
  const percent = questions.length > 0 ? Math.round((Math.min(answeredCount, questions.length) / questions.length) * 100) : 0

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

  if (loading) return <PageLoader label="Loading the interest test…" />
  if (loadError) return <PageError message={loadError} />

  return (
    <main>
      <PageHeader
        eyebrow="Step 2 of 2"
        title="Interest test"
        description="Pick whichever option feels closest. Each answer saves right away, so you can close this and pick up right where you left off."
      />

      {/* Progress sits just under the sticky site header. */}
      <div className="sticky top-16 z-30 border-b border-slate-200/70 bg-white/90 backdrop-blur-lg">
        <div className="container-page flex items-center gap-4 py-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-linear-to-r from-indigo-500 to-violet-500 transition-all duration-500"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="shrink-0 text-sm font-medium text-slate-700 tabular-nums" role="status" aria-live="polite">
            {answeredCount} of {questions.length} answered
          </p>
        </div>
      </div>

      <div className="container-page max-w-3xl py-8 lg:py-10">
        <div className="space-y-3">
          {saveError && <Alert tone="error">{saveError}</Alert>}
          {complete && (
            <div className="card flex flex-col gap-4 border-emerald-200 bg-emerald-50/60 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
                  <Icon name="check" className="size-5" strokeWidth={2.5} />
                </span>
                <div>
                  <p className="font-semibold text-emerald-900">You've answered every question</p>
                  <p className="text-sm text-emerald-800">Your interest chart is ready.</p>
                </div>
              </div>
              <Link to="/my-results" className="btn btn-primary">
                View your results
                <Icon name="arrowRight" className="size-4" />
              </Link>
            </div>
          )}
        </div>

        <ol className={`space-y-4 ${saveError || complete ? 'mt-6' : ''}`}>
          {questions.map((question, index) => {
            const isSaving = savingQuestionId === question.id
            const isAnswered = answers[question.id] != null
            return (
              <li key={question.id} className="card p-5 sm:p-6">
                <fieldset>
                  <legend className="flex w-full items-start gap-3">
                    <span
                      className={`grid size-8 shrink-0 place-items-center rounded-lg text-sm font-semibold transition ${
                        isAnswered ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className="pt-1 font-medium leading-snug text-slate-900">{question.text}</span>
                  </legend>

                  <div className="mt-4 grid gap-2 sm:grid-cols-2">
                    {question.options.map((option) => (
                      <label
                        key={option.id}
                        className="group flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50/40 has-checked:border-indigo-600 has-checked:bg-indigo-50 has-checked:text-indigo-900 has-focus-visible:ring-4 has-focus-visible:ring-indigo-500/20 has-disabled:cursor-wait"
                      >
                        <input
                          type="radio"
                          className="sr-only"
                          name={`question-${question.id}`}
                          checked={answers[question.id] === option.id}
                          onChange={() => choose(question.id, option.id)}
                          disabled={isSaving}
                        />
                        <span
                          className="grid size-5 shrink-0 place-items-center rounded-full border-2 border-slate-300 transition group-has-checked:border-indigo-600 group-has-checked:bg-indigo-600"
                          aria-hidden="true"
                        >
                          <span className="size-1.5 rounded-full bg-white opacity-0 group-has-checked:opacity-100" />
                        </span>
                        <span className="leading-snug">{option.text}</span>
                      </label>
                    ))}
                  </div>

                  <div className="mt-3 h-4 text-xs">
                    {isSaving && (
                      <span className="inline-flex items-center gap-1.5 text-slate-500">
                        <Spinner className="size-3" />
                        Saving…
                      </span>
                    )}
                  </div>
                </fieldset>
              </li>
            )
          })}
        </ol>
      </div>
    </main>
  )
}
