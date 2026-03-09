import axios from 'axios'
import type { DataPoint, EtlBatchResult, Indicator, LatestData, Region } from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
})

export const getRegions = async (): Promise<Region[]> => {
  const { data } = await api.get<Region[]>('/regions')
  return data
}

export const getIndicators = async (theme?: string): Promise<Indicator[]> => {
  const { data } = await api.get<Indicator[]>('/indicators', {
    params: theme ? { theme } : undefined,
  })
  return data
}

export const getThemes = async (): Promise<string[]> => {
  const { data } = await api.get<string[]>('/themes')
  return data
}

type GetDataParams = {
  regionId: number
  indicatorId: number
  startYear: number
  endYear: number
}

export const getData = async (params: GetDataParams): Promise<DataPoint[]> => {
  const { data } = await api.get<DataPoint[]>('/data', {
    params: {
      region_id: params.regionId,
      indicator_id: params.indicatorId,
      start_year: params.startYear,
      end_year: params.endYear,
    },
  })
  return data
}

export const getLatestData = async (
  regionId: number,
  indicatorId: number,
): Promise<LatestData> => {
  const { data } = await api.get<LatestData>('/data/latest', {
    params: {
      region_id: regionId,
      indicator_id: indicatorId,
    },
  })
  return data
}

export const runEtl = async (): Promise<void> => {
  await api.post('/etl/run')
}

export const runEtlAggregates = async (): Promise<void> => {
  await api.post('/etl/run-aggregates')
}

export const runEtlAll = async (): Promise<void> => {
  await Promise.all([runEtl(), runEtlAggregates()])
}

export const getEtlAreas = async (): Promise<string[]> => {
  const { data } = await api.get<string[]>('/etl/areas')
  return data
}

export const runEtlSequential = async (
  areas?: string[],
  startYear?: number,
): Promise<EtlBatchResult> => {
  const params: string[] = []
  if (areas?.length) {
    params.push(`areas=${encodeURIComponent(areas.join(','))}`)
  }
  if (startYear) {
    params.push(`start_year=${startYear}`)
  }
  const query = params.length ? `?${params.join('&')}` : ''
  const { data } = await api.post<EtlBatchResult>(`/etl/run-sequential${query}`)
  return data
}
