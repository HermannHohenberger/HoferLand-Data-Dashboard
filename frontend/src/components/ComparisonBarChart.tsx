type ComparisonRow = {
  name: string
  currentValue: number | null
  changeAbsolute: number | null
  changePercent: number | null
  color: string
}

type ComparisonBarChartProps = {
  rows: ComparisonRow[]
  comparisonYear: number | null
  comparisonYears: number[]
  onComparisonYearChange: (year: number) => void
  fractionDigits?: number
}

export function ComparisonBarChart({
  rows,
  comparisonYear,
  comparisonYears,
  onComparisonYearChange,
  fractionDigits = 0,
}: ComparisonBarChartProps) {
  const formatNumber = (value: number | null) => {
    if (value === null) {
      return 'N/A'
    }
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(value)
  }

  const formatPercent = (value: number | null) => {
    if (value === null) {
      return 'N/A'
    }
    return `${value.toFixed(2)} %`
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-gray-700">Veraenderung</p>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Vergleichsjahr</label>
          <select
            className="rounded-md border border-gray-300 px-2 py-1 text-xs"
            value={comparisonYear ?? ''}
            onChange={(event) => onComparisonYearChange(Number(event.target.value))}
            disabled={!comparisonYears.length}
          >
            {comparisonYears.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-600">
              <th className="px-3 py-2 font-medium">Region</th>
              <th className="px-3 py-2 font-medium">Aktueller Wert</th>
              <th className="px-3 py-2 font-medium">Veraenderung absolut</th>
              <th className="px-3 py-2 font-medium">Veraenderung in %</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-b border-gray-100">
                <td className="px-3 py-2" style={{ borderLeft: `4px solid ${row.color}` }}>
                  {row.name}
                </td>
                <td className="px-3 py-2">{formatNumber(row.currentValue)}</td>
                <td className="px-3 py-2">{formatNumber(row.changeAbsolute)}</td>
                <td className="px-3 py-2">{formatPercent(row.changePercent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
