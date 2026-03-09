type TimeRangeFilterProps = {
  startYear: number
  endYear: number
  minYear: number
  maxYear: number
  onStartYearChange: (year: number) => void
  onEndYearChange: (year: number) => void
}

export function TimeRangeFilter({
  startYear,
  endYear,
  minYear,
  maxYear,
  onStartYearChange,
  onEndYearChange,
}: TimeRangeFilterProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-gray-700">Zeitraum</p>
      <div>
        <label className="mb-1 block text-xs uppercase tracking-wide text-gray-500">
          Startjahr
        </label>
        <input
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          type="number"
          min={minYear}
          max={endYear}
          value={startYear}
          onChange={(event) => onStartYearChange(Number(event.target.value))}
        />
      </div>
      <div>
        <label className="mb-1 block text-xs uppercase tracking-wide text-gray-500">
          Endjahr
        </label>
        <input
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          type="number"
          min={startYear}
          max={maxYear}
          value={endYear}
          onChange={(event) => onEndYearChange(Number(event.target.value))}
        />
      </div>
    </div>
  )
}
