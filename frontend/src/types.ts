export type Region = {
  id: number
  ags_code: string
  name: string
  type: string
}

export type Indicator = {
  id: number
  code: string
  theme: string
  name: string
  description: string | null
  unit: string
  genesis_table: string
}

export type DataPoint = {
  year: number
  value: number
}

export type LatestData = {
  region_id: number
  year: number
  value: number
  change_absolute: number | null
  change_percent: number | null
}

export type EtlAreaResult = {
  area: string
  inserted_or_updated: number
  status?: string
  message?: string | null
}

export type EtlBatchResult = {
  indicator_id: number
  total_inserted_or_updated: number
  results: EtlAreaResult[]
}
