const STYLES = {
  Eligible: { pill: 'bg-emerald-50 text-emerald-700 ring-emerald-200', dot: 'bg-emerald-500' },
  Conditional: { pill: 'bg-amber-50 text-amber-800 ring-amber-200', dot: 'bg-amber-500' },
  'Not Eligible': { pill: 'bg-red-50 text-red-700 ring-red-200', dot: 'bg-red-500' },
}
const FALLBACK = { pill: 'bg-slate-100 text-slate-700 ring-slate-200', dot: 'bg-slate-400' }

export function VerdictPill({ verdict }) {
  const style = STYLES[verdict] || FALLBACK
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 self-start rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style.pill}`}
    >
      <span className={`size-1.5 rounded-full ${style.dot}`} aria-hidden="true" />
      {verdict}
    </span>
  )
}

export function ReasonList({ reasons = [] }) {
  if (reasons.length === 0) return null
  return (
    <ul className="mt-2 space-y-1 text-xs text-slate-500">
      {reasons.map((reason) => (
        <li key={reason} className="flex gap-2">
          <span className="mt-1.5 size-1 shrink-0 rounded-full bg-slate-300" aria-hidden="true" />
          {reason}
        </li>
      ))}
    </ul>
  )
}

// Verdict badge + its reasons (PRD T2: "always with reasons"). Best Fit only
// ever shows Eligible/Conditional programs, but the badge itself supports
// all three verdicts so it stays correct if that ever changes.
export default function EligibilityBadge({ verdict, reasons = [] }) {
  return (
    <div>
      <VerdictPill verdict={verdict} />
      <ReasonList reasons={reasons} />
    </div>
  )
}
