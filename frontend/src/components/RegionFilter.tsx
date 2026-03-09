import type { Region } from '../types'

type RegionFilterProps = {
  regions: Region[]
  selectedRegionId: number | null
  onChange: (regionId: number) => void
}

export function RegionFilter({
  regions,
  selectedRegionId,
  onChange,
}: RegionFilterProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">Region</label>
      <select
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        value={selectedRegionId ?? ''}
        onChange={(event) => onChange(Number(event.target.value))}
      >
        {regions.map((region) => (
          <option key={region.id} value={region.id}>
            {region.name}
          </option>
        ))}
      </select>
    </div>
  )
}
