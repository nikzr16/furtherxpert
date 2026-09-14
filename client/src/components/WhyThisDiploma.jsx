import { Icon } from './ui'

// "Why this diploma?" (result explanations PRD): an open/close section under
// one Best Fit diploma. The backend writes every sentence
// (services/explanations.py); this only lays them out, like ReasonList.
export default function WhyThisDiploma({ why }) {
  if (!why) return null

  return (
    <details className="group mt-3 rounded-xl border border-slate-200 bg-slate-50/60 open:bg-white">
      <summary className="flex cursor-pointer list-none items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-indigo-700 transition hover:bg-indigo-50/60 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/20 [&::-webkit-details-marker]:hidden">
        <Icon name="info" className="size-4 shrink-0" />
        Why this diploma?
        <Icon name="chevronDown" className="ml-auto size-4 shrink-0 transition group-open:rotate-180" />
      </summary>

      <div className="space-y-5 border-t border-slate-200 px-4 py-4 text-sm leading-relaxed text-slate-700">
        <section>
          <h4 className="font-semibold text-slate-900">Why it matches you</h4>
          <ul className="mt-1.5 space-y-1.5">
            {why.match.map((line) => (
              <li key={line} className="flex gap-2">
                <Icon name="sparkles" className="mt-0.5 size-4 shrink-0 text-violet-500" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h4 className="font-semibold text-slate-900">How you meet the entry rules</h4>
          <div className="mt-2 grid gap-4 md:grid-cols-2">
            {why.rules.map((section) => (
              <div key={section.title}>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{section.title}</p>
                <ul className="mt-1.5 space-y-1">
                  {section.lines.map((line, index) =>
                    // A line ending in ":" introduces the lines under it ("You
                    // meet one of the allowed options:"), so it gets no tick.
                    line.endsWith(':') ? (
                      <li key={index} className="pt-1 text-slate-500">
                        {line}
                      </li>
                    ) : (
                      <li key={index} className="flex gap-2">
                        <Icon name="check" className="mt-0.5 size-4 shrink-0 text-emerald-600" strokeWidth={2.25} />
                        <span>{line}</span>
                      </li>
                    ),
                  )}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h4 className="font-semibold text-slate-900">Anything still needed</h4>
          <ul className="mt-1.5 space-y-1">
            {why.still_needed.map((line) => (
              <li key={line} className="flex gap-2">
                <Icon name="clock" className="mt-0.5 size-4 shrink-0 text-slate-400" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </section>

        <p className="border-t border-slate-100 pt-3 text-slate-500">{why.position}</p>
      </div>
    </details>
  )
}
