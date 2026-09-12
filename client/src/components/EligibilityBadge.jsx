const STYLES = {
  Eligible: 'bg-green-100 text-green-800 border-green-300',
  Conditional: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Not Eligible': 'bg-red-100 text-red-800 border-red-300',
}

// Verdict badge + its reasons (PRD T2: "always with reasons"). Best Fit only
// ever shows Eligible/Conditional programs, but the badge itself supports
// all three verdicts so it stays correct if that ever changes.
export default function EligibilityBadge({ verdict, reasons = [] }) {
  const style = STYLES[verdict] || 'bg-gray-100 text-gray-800 border-gray-300'

  return (
    <div>
      <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${style}`}>{verdict}</span>
      {reasons.length > 0 && (
        <ul className="mt-1 list-inside list-disc text-xs text-gray-600">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
