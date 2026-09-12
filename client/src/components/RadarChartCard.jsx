import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'

// A Recharts radar chart plus a real, always-reachable <table> equivalent
// (PRD T7: "each chart has a text-table version for screen readers",
// WCAG AA). The table lives inside a native <details> so it's collapsed by
// default without ever being display:none -- it's still in the page, still
// reachable by keyboard and by a screen reader's browse mode, and opening it
// needs no custom JavaScript.
export default function RadarChartCard({ title, data, scoreLabel = 'Score', emptyMessage }) {
  const hasData = data && data.length > 0

  return (
    <section className="rounded border border-gray-200 p-4" aria-label={title}>
      <h3 className="text-lg font-semibold">{title}</h3>

      {!hasData && <p className="mt-2 text-gray-500">{emptyMessage}</p>}

      {hasData && (
        <>
          <div className="mt-2 h-72 w-full" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={data} outerRadius="75%">
                <PolarGrid />
                <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar name={scoreLabel} dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <details className="mt-3" open>
            <summary className="cursor-pointer text-sm font-medium text-blue-700">
              View as a table
            </summary>
            <table className="mt-2 w-full border-collapse text-sm">
              <caption className="sr-only">{title}, as a table</caption>
              <thead>
                <tr className="border-b border-gray-300 text-left">
                  <th scope="col" className="py-1 pr-4">
                    Area
                  </th>
                  <th scope="col" className="py-1">
                    {scoreLabel}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => (
                  <tr key={row.name} className="border-b border-gray-100">
                    <td className="py-1 pr-4">{row.name}</td>
                    <td className="py-1">{row.score}%</td>
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
