import { Link } from 'react-router-dom'
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Icon } from './ui'

const VARIANTS = {
  excel: { color: '#4f46e5', icon: 'academicCap', iconBox: 'bg-indigo-50 text-indigo-600' },
  love: { color: '#e11d48', icon: 'heart', iconBox: 'bg-rose-50 text-rose-600' },
}

const LINE_HEIGHT = 13

// Long area names ("Healthcare & Social Services") are split at the "&" so a
// label never pushes past the chart edge.
function splitLabel(name) {
  const joint = name.indexOf(' & ')
  if (name.length > 12 && joint !== -1) return [`${name.slice(0, joint)} &`, name.slice(joint + 3)]
  return [name]
}

// Spoke label: the area name in small grey text with its score underneath.
// Labels above the centre grow upward, labels below grow downward, and side
// labels are centred on the spoke, so none of them overlap the web itself.
function SpokeLabel({ x, y, cy, textAnchor, payload, scores, color }) {
  const lines = splitLabel(payload.value)
  const score = scores[payload.value]
  const lineCount = lines.length + 1
  let firstDy
  if (y < cy - 4) firstDy = -(lineCount - 1) * LINE_HEIGHT - 4
  else if (y > cy + 4) firstDy = 12
  else firstDy = -((lineCount - 1) * LINE_HEIGHT) / 2 + 4

  return (
    <text x={x} y={y} textAnchor={textAnchor}>
      {lines.map((line, index) => (
        <tspan key={line} x={x} dy={index === 0 ? firstDy : LINE_HEIGHT} fill="#64748b" fontSize={11}>
          {line}
        </tspan>
      ))}
      <tspan x={x} dy={LINE_HEIGHT + 1} fill={score == null ? '#94a3b8' : color} fontSize={12} fontWeight={600}>
        {score == null ? 'N/A' : `${score}%`}
      </tspan>
    </text>
  )
}

// A Recharts radar chart plus a real, always-reachable <table> equivalent
// (PRD T7: "each chart has a text-table version for screen readers",
// WCAG AA). The table is visually hidden with `sr-only` (never display:none),
// so it stays in the page for screen readers while sighted students read the
// scores off the spoke labels (decision 0018).
export default function RadarChartCard({
  title,
  subtitle,
  data,
  variant = 'excel',
  scoreLabel = 'Score',
  emptyMessage,
  emptyAction,
}) {
  const hasData = data && data.length > 0
  const style = VARIANTS[variant]
  const scores = hasData ? Object.fromEntries(data.map((row) => [row.name, row.score])) : {}
  // A row with `score: null` has no value (for example a subject group the
  // student took no subjects in). It's drawn at the centre with no dot, and
  // labelled "N/A" instead of a percentage (decision 0019).
  const chartData = hasData ? data.map((row) => ({ ...row, value: row.score ?? 0 })) : []
  const gradientId = `radar-fill-${variant}`

  return (
    <section className="card flex flex-col p-5 sm:p-6" aria-label={title}>
      <div className="flex items-start gap-3">
        <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${style.iconBox}`}>
          <Icon name={style.icon} className="size-5" />
        </span>
        <div>
          <h2 className="font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
      </div>

      {!hasData && (
        <div className="mt-5 flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-14 text-center">
          <Icon name="chartBar" className="size-8 text-slate-300" />
          <p className="mt-3 max-w-xs text-sm text-slate-600">{emptyMessage}</p>
          {emptyAction && (
            <Link to={emptyAction.to} className="btn btn-primary btn-sm mt-4">
              {emptyAction.label}
              <Icon name="arrowRight" className="size-3.5" />
            </Link>
          )}
        </div>
      )}

      {hasData && (
        <>
          <div className="mt-2 h-80 w-full sm:h-[22rem]" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData} outerRadius="66%" margin={{ top: 24, right: 36, bottom: 24, left: 36 }}>
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={style.color} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={style.color} stopOpacity={0.12} />
                  </linearGradient>
                </defs>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  tick={(props) => <SpokeLabel {...props} scores={scores} color={style.color} />}
                />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} tickCount={5} />
                <Radar
                  name={scoreLabel}
                  dataKey="value"
                  stroke={style.color}
                  strokeWidth={2}
                  fill={`url(#${gradientId})`}
                  fillOpacity={1}
                  dot={(props) =>
                    chartData[props.index]?.score == null ? (
                      <g key={`dot-${props.index}`} />
                    ) : (
                      <circle key={`dot-${props.index}`} cx={props.cx} cy={props.cy} r={3} fill={style.color} />
                    )
                  }
                  activeDot={{ r: 5 }}
                />
                <Tooltip
                  formatter={(value, _name, item) => [item.payload.score == null ? 'N/A' : `${value}%`, scoreLabel]}
                  contentStyle={{
                    borderRadius: 12,
                    border: '1px solid #e2e8f0',
                    boxShadow: '0 8px 24px rgb(15 23 42 / 0.08)',
                    fontSize: 12,
                    fontFamily: 'inherit',
                  }}
                  labelStyle={{ color: '#0f172a', fontWeight: 600 }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <table className="sr-only">
            <caption>{title}, as a table</caption>
            <thead>
              <tr>
                <th scope="col">Area</th>
                <th scope="col">{scoreLabel}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.name}>
                  <td>{row.name}</td>
                  <td>{row.score == null ? 'N/A, no subjects taken' : `${row.score}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  )
}
