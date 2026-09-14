import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from 'recharts'
import { getPrograms, getUniversities } from '../api'
import { useAuth } from '../context/AuthContext'
import { Badge, Icon } from '../components/ui'

// Illustrative numbers for the hero preview only -- clearly labelled as an
// example, never a real student's result.
const EXAMPLE_CHART = [
  { name: 'Science', score: 84 },
  { name: 'Business', score: 62 },
  { name: 'Arts', score: 48 },
  { name: 'Health', score: 74 },
  { name: 'Media', score: 40 },
  { name: 'Education', score: 58 },
]

const STEPS = [
  {
    icon: 'document',
    title: 'Add your SPM results',
    body: 'Enter your subjects and grades. Bahasa Melayu and Sejarah are required for every UPU program.',
  },
  {
    icon: 'heart',
    title: 'Take the interest test',
    body: 'Answer 20 quick questions. Every answer saves as you go, so you can stop and come back anytime.',
  },
  {
    icon: 'chartBar',
    title: 'See where you fit',
    body: 'Get two spider charts, a best-fit shortlist, and the diploma programs you qualify for.',
  },
]

const FEATURES = [
  {
    icon: 'academicCap',
    title: 'What you’ll excel in',
    body: 'A spider chart of your strongest subject groups, worked out from your real SPM grades.',
  },
  {
    icon: 'heart',
    title: 'What you’ll love',
    body: 'Nine interest areas scored from your test answers, so you can see what really pulls you in.',
  },
  {
    icon: 'shield',
    title: 'Official UPU eligibility',
    body: 'Programs are checked against the official syarat am and syarat khas, with the reasons shown.',
  },
  {
    icon: 'sparkles',
    title: 'A summary in plain words',
    body: 'A short AI-written summary explains what your charts mean, without the jargon.',
  },
]

export default function Home() {
  const { isAuthenticated, initializing } = useAuth()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([getPrograms(), getUniversities()])
      .then(([programs, universities]) => {
        if (!cancelled) setStats({ programs: programs.length, universities: universities.length })
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200/70 bg-white">
        <div className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" aria-hidden="true" />
        <div
          className="pointer-events-none absolute -top-40 left-1/2 h-[28rem] w-[56rem] -translate-x-1/2 rounded-full bg-linear-to-r from-indigo-200/50 via-violet-200/40 to-rose-200/40 blur-3xl"
          aria-hidden="true"
        />
        <div className="container-page relative grid items-center gap-14 py-16 sm:py-20 lg:grid-cols-[1.1fr_1fr] lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/80 px-3 py-1 text-xs font-medium text-indigo-700 shadow-xs">
              <Icon name="sparkles" className="size-3.5" />
              Built for Malaysian SPM leavers
            </span>
            <h1 className="mt-6 text-4xl leading-[1.1] font-semibold tracking-tight text-slate-900 sm:text-5xl lg:text-[3.5rem]">
              Find the diploma you’ll{' '}
              <span className="bg-linear-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">excel in</span>{' '}
              and{' '}
              <span className="bg-linear-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent">love</span>.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
              FurtherXpert turns your SPM results and a short interest test into two clear charts, a best-fit
              shortlist, and the official UPU diploma programs you qualify for.
            </p>

            <div className="mt-8 flex min-h-12 flex-wrap gap-3">
              {!initializing && !isAuthenticated && (
                <>
                  <Link to="/register" className="btn btn-primary btn-lg">
                    Get started
                    <Icon name="arrowRight" className="size-4" />
                  </Link>
                  <Link to="/explore" className="btn btn-secondary btn-lg">
                    Browse programs
                  </Link>
                </>
              )}
              {!initializing && isAuthenticated && (
                <>
                  <Link to="/my-results" className="btn btn-primary btn-lg">
                    View my results
                    <Icon name="arrowRight" className="size-4" />
                  </Link>
                  <Link to="/results" className="btn btn-secondary btn-lg">
                    Update SPM results
                  </Link>
                  <Link to="/interest-test" className="btn btn-ghost btn-lg">
                    Interest test
                  </Link>
                </>
              )}
            </div>

            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-500">
              {['Official UPU entry rules', '20-question interest test', 'Browse without an account'].map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <Icon name="checkCircle" className="size-4 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <HeroPreview />
        </div>
      </section>

      {/* Stats */}
      {stats && (
        <section className="border-b border-slate-200/70 bg-slate-50">
          <dl className="container-page grid grid-cols-2 gap-6 py-10 text-center md:grid-cols-4">
            <Stat value={stats.programs} label="Diploma programs" />
            <Stat value={stats.universities} label="Public universities" />
            <Stat value={9} label="Interest areas" />
            <Stat value={20} label="Test questions" />
          </dl>
        </section>
      )}

      {/* How it works */}
      <section className="container-page py-20 sm:py-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold text-indigo-600">How it works</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Three steps to a clear shortlist
          </h2>
          <p className="mt-4 text-slate-600">No guesswork. Just your grades, your interests, and the official rules.</p>
        </div>
        <ol className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((step, index) => (
            <li key={step.title} className="card relative p-6 sm:p-7">
              <span className="absolute top-6 right-6 text-5xl leading-none font-semibold text-slate-100 select-none">
                {index + 1}
              </span>
              <span className="relative grid size-11 place-items-center rounded-xl bg-indigo-600 text-white shadow-sm shadow-indigo-600/30">
                <Icon name={step.icon} className="size-5" />
              </span>
              <h3 className="relative mt-5 text-lg font-semibold text-slate-900">{step.title}</h3>
              <p className="relative mt-2 text-sm leading-relaxed text-slate-600">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Features */}
      <section className="border-y border-slate-200/70 bg-white">
        <div className="container-page grid gap-12 py-20 sm:py-24 lg:grid-cols-[1fr_1.4fr] lg:gap-16">
          <div>
            <p className="text-sm font-semibold text-indigo-600">What you get</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
              Everything you need to choose with confidence
            </h2>
            <p className="mt-4 leading-relaxed text-slate-600">
              See your strengths and interests side by side, then go straight to the programs that match both.
            </p>
            <Link to="/explore" className="btn btn-secondary mt-8">
              Explore all programs
              <Icon name="arrowRight" className="size-4" />
            </Link>
          </div>
          <div className="grid gap-x-8 gap-y-10 sm:grid-cols-2">
            {FEATURES.map((feature) => (
              <div key={feature.title}>
                <span className="grid size-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100">
                  <Icon name={feature.icon} className="size-5" />
                </span>
                <h3 className="mt-4 font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{feature.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Closing call to action */}
      <section className="container-page py-20 sm:py-24">
        <div className="relative overflow-hidden rounded-3xl bg-linear-to-br from-indigo-600 via-indigo-700 to-violet-800 px-6 py-14 text-center shadow-xl shadow-indigo-900/20 sm:px-16">
          <div className="bg-grid pointer-events-none absolute inset-0 opacity-30 invert" aria-hidden="true" />
          <div className="relative mx-auto max-w-2xl">
            <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Ready to find your path?</h2>
            <p className="mt-4 text-indigo-100">
              It takes about as long as a lunch break, and your progress saves as you go.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                to={isAuthenticated ? '/my-results' : '/register'}
                className="btn btn-lg bg-white text-indigo-700 shadow-sm hover:bg-indigo-50"
              >
                {isAuthenticated ? 'Go to my results' : 'Create your account'}
                <Icon name="arrowRight" className="size-4" />
              </Link>
              <Link to="/explore" className="btn btn-lg text-white ring-1 ring-white/30 hover:bg-white/10">
                Browse programs
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

function Stat({ value, label }) {
  return (
    <div>
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="order-first text-3xl font-semibold tracking-tight text-slate-900">{value}</dd>
    </div>
  )
}

function HeroPreview() {
  return (
    <div className="relative mx-auto w-full max-w-md lg:max-w-none" aria-hidden="true">
      <div className="absolute -inset-4 rounded-[2rem] bg-linear-to-br from-indigo-100 to-rose-100 opacity-60 blur-2xl" />
      <div className="card relative p-5 shadow-xl shadow-slate-900/5 sm:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-rose-50 text-rose-600">
              <Icon name="heart" className="size-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">What you’re likely to love</p>
              <p className="text-xs text-slate-500">Example result</p>
            </div>
          </div>
          <Badge tone="slate">Preview</Badge>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={EXAMPLE_CHART} outerRadius="70%">
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="name" tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar
                dataKey="score"
                stroke="#e11d48"
                strokeWidth={2}
                fill="#e11d48"
                fillOpacity={0.18}
                dot={{ r: 3, fill: '#e11d48', strokeWidth: 0 }}
                isAnimationActive={false}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between rounded-xl border border-violet-100 bg-violet-50/60 px-3.5 py-2.5">
            <span className="text-sm font-medium text-slate-800">Science &amp; Technology</span>
            <Badge tone="violet" icon="star">
              Sweet spot
            </Badge>
          </div>
          <div className="flex items-center justify-between rounded-xl border border-slate-200 px-3.5 py-2.5">
            <span className="text-sm font-medium text-slate-800">Healthcare &amp; Social Services</span>
            <Badge tone="rose">Likely to love</Badge>
          </div>
        </div>
      </div>
    </div>
  )
}
