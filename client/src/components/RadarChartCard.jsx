import { Link } from 'react-router-dom'
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Icon } from './ui'

const VARIANTS = {
  excel: { color: '#4f46e5', icon: 'academicCap', iconBox: 'bg-indigo-50 text-indigo-600', bar: 'bg-indigo-500' },
  love: { color: '#e11d48', icon: 'heart', iconBox: 'bg-rose-50 text-rose-600', bar: 'bg-rose-500' },
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
      <tspan x={x} dy={LINE_HEIGHT + 1} fill={color} fontSize={12} fontWeight={600}>
        {scores[payload.value]}%
      </tspan>
    </text>
  )
}

// A Recharts radar chart plus a real, always-reachable <table> equivalent
// (PRD T7: "each chart has a text-table version for screen readers",
// WCAG AA). The table lives inside a native <details> so it's collapsed by
// default without ever being display:none -- it's still in the page, still
// reachable by keyboard and by a screen reader's browse mode, and opening it
// needs no custom JavaScript.
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
              <RadarChart data={data} outerRadius="66%" margin={{ top: 24, right: 36, bottom: 24, left: 36 }}>
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
                  dataKey="score"
                  stroke={style.color}
                  strokeWidth={2}
                  fill={`url(#${gradientId})`}
                  fillOpacity={1}
                  dot={{ r: 3, fill: style.color, strokeWidth: 0 }}
                  activeDot={{ r: 5 }}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, scoreLabel]}
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

          <details className="group mt-4 border-t border-slate-100 pt-3">
            <summary className="flex cursor-pointer list-none items-center justify-between rounded-lg py-1 text-sm font-medium text-slate-600 transition hover:text-slate-900">
              View as a table
              <Icon name="chevronDown" className="size-4 transition group-open:rotate-180" />
            </summary>
            <table className="mt-3 w-full border-collapse text-sm">
              <caption className="sr-only">{title}, as a table</caption>
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs tracking-wide text-slate-500 uppercase">
                  <th scope="col" className="py-2 pr-4 font-medium">
                    Area
                  </th>
                  <th scope="col" className="py-2 text-right font-medium">
                    {scoreLabel}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => (
                  <tr key={row.name} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-slate-700">{row.name}</td>
                    <td className="py-2">
                      <div className="flex items-center justify-end gap-3">
                        <span className="hidden h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 sm:block">
                          <span className={`block h-full rounded-full ${style.bar}`} style={{ width: `${row.score}%` }} />
                        </span>
                        <span className="w-10 text-right font-medium text-slate-900 tabular-nums">{row.score}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      )}
    </section>
  )
}
