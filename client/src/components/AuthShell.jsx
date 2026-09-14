import { Icon, LogoMark } from './ui'

const POINTS = [
  'See your strongest subject groups from your SPM grades',
  'Find the interest areas you are most likely to love',
  'Check which UPU diploma programs you qualify for',
]

// Two-panel layout for the log in and register pages: a branded panel on
// large screens, the form card on the right.
export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <main className="container-page grid min-h-[calc(100vh-4rem)] items-center gap-10 py-10 lg:grid-cols-2 lg:py-16">
      <section className="relative hidden h-full min-h-[34rem] overflow-hidden rounded-3xl bg-linear-to-br from-indigo-600 via-indigo-700 to-violet-800 p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="bg-grid pointer-events-none absolute inset-0 opacity-40 invert" aria-hidden="true" />
        <div
          className="pointer-events-none absolute -top-24 -right-24 size-80 rounded-full bg-violet-400/30 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative">
          <span className="inline-flex rounded-2xl bg-white/10 p-2 ring-1 ring-white/20">
            <LogoMark className="size-9" />
          </span>
          <h2 className="mt-8 max-w-sm text-3xl leading-tight font-semibold tracking-tight">
            Your next step after SPM, mapped out.
          </h2>
          <p className="mt-3 max-w-sm text-indigo-100">
            One account turns your grades and interests into a clear shortlist of diploma programs.
          </p>
        </div>
        <ul className="relative space-y-4">
          {POINTS.map((point) => (
            <li key={point} className="flex items-start gap-3 text-sm text-indigo-50">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-white/15 ring-1 ring-white/25">
                <Icon name="check" className="size-3.5" strokeWidth={2.5} />
              </span>
              {point}
            </li>
          ))}
        </ul>
      </section>

      <section className="mx-auto w-full max-w-md">
        <div className="card p-6 sm:p-8">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
        {footer && <p className="mt-6 text-center text-sm text-slate-500">{footer}</p>}
      </section>
    </main>
  )
}
