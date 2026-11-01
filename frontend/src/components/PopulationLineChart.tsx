import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DataPoint } from '../types'
import { getRegionColor } from '../constants/regionColors'

type RegionSeries = {
  name: string
  points: DataPoint[]
}

type PopulationLineChartProps = {
  series: RegionSeries[]
  title?: string
  fractionDigits?: number
}

export function PopulationLineChart({
  series,
  title = 'Bevölkerungsentwicklung',
  fractionDigits = 0,
}: PopulationLineChartProps) {
  const formatTick = (value: number) =>
    new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(value)

  const years = Array.from(
    new Set(series.flatMap((regionSeries) => regionSeries.points.map((point) => point.year))),
  ).sort((a, b) => a - b)

  const chartData = years.map((year) => {
    const row: Record<string, number | null> = { year }
    series.forEach((regionSeries, index) => {
      const point = regionSeries.points.find((entry) => entry.year === year)
      row[`series-${index}`] = point?.value ?? null
    })
    return row
  })

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="mb-4 text-sm font-medium text-gray-700">{title}</p>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 12, left: 16, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis width={96} tickFormatter={formatTick} tick={{ fontSize: 12, fill: '#374151' }} />
            <Tooltip
              formatter={(value, _name, item) => {
                const formatted = typeof value === 'number' ? formatTick(value) : 'N/A'
                return [formatted, String(item?.name ?? '')]
              }}
            />
            {series.map((regionSeries, index) => (
              <Line
                key={`${regionSeries.name}-${index}`}
                type="monotone"
                dataKey={`series-${index}`}
                name={regionSeries.name}
                stroke={getRegionColor(regionSeries.name, index)}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-sm">
        {series.map((regionSeries, index) => {
          const color = getRegionColor(regionSeries.name, index)
          return (
            <li key={`${regionSeries.name}-${index}`} className="flex items-center gap-2">
              <span className="inline-block h-0.5 w-6" style={{ backgroundColor: color }} />
              <span style={{ color }}>{regionSeries.name}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
