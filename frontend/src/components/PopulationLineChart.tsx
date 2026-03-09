import {
  CartesianGrid,
  Legend,
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
  title = 'Bevoelkerungsentwicklung',
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
    for (const regionSeries of series) {
      const point = regionSeries.points.find((entry) => entry.year === year)
      row[regionSeries.name] = point?.value ?? null
    }
    return row
  })

  return (
    <div className="h-[460px] rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="mb-4 text-sm font-medium text-gray-700">{title}</p>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: 16, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis width={96} tickFormatter={formatTick} tick={{ fontSize: 12, fill: '#374151' }} />
          <Tooltip
            formatter={(value) => (typeof value === 'number' ? formatTick(value) : 'N/A')}
          />
          <Legend />
          {series.map((regionSeries, index) => (
            <Line
              key={regionSeries.name}
              type="monotone"
              dataKey={regionSeries.name}
              stroke={getRegionColor(regionSeries.name, index)}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
