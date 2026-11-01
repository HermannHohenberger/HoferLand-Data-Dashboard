import { useEffect, useMemo, useState } from 'react'
import { getData, getIndicators, getRegions, getThemes } from '../api/client'
import { ComparisonBarChart } from '../components/ComparisonBarChart'
import { KpiCard } from '../components/KpiCard'
import { Layout } from '../components/Layout'
import { PopulationLineChart } from '../components/PopulationLineChart'
import { TimeRangeFilter } from '../components/TimeRangeFilter'
import type { DataPoint, Indicator, Region } from '../types'
import { getRegionColor } from '../constants/regionColors'
import { displayText } from '../utils/displayText'

const CURRENT_YEAR = new Date().getFullYear()
const LAST_COMPLETE_YEAR = CURRENT_YEAR - 1
const DEFAULT_REGION_NAMES = ['Hof, kreisfreie Stadt', 'Hof, Landkreis']
const DEFAULT_THEME = 'Bevoelkerung'
const THEME_DEFAULT_INDICATOR_CODE: Record<string, string> = {
  Bevoelkerung: 'BEV_TOTAL',
  Arbeitsmarkt: 'AL_TOTAL',
}

function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

export function Dashboard() {
  const [regions, setRegions] = useState<Region[]>([])
  const [themes, setThemes] = useState<string[]>([])
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null)
  const [themeIndicators, setThemeIndicators] = useState<Indicator[]>([])
  const [selectedAreaIds, setSelectedAreaIds] = useState<number[]>([])
  const [selectedRegionIds, setSelectedRegionIds] = useState<number[]>([])
  const [startYear, setStartYear] = useState(2014)
  const [endYear, setEndYear] = useState(LAST_COMPLETE_YEAR)
  const [lineSeries, setLineSeries] = useState<
    Array<{
      regionId: number
      regionName: string
      indicatorId: number
      indicatorCode: string
      indicatorName: string
      points: DataPoint[]
    }>
  >([])
  const [comparisonYear, setComparisonYear] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const selectedIndicators = useMemo(
    () => themeIndicators.filter((indicator) => selectedAreaIds.includes(indicator.id)),
    [themeIndicators, selectedAreaIds],
  )
  const selectedIndicator = useMemo(
    () => (selectedIndicators.length ? selectedIndicators[0] : null),
    [selectedIndicators],
  )
  const primaryRegionSeries = useMemo(
    () =>
      selectedRegionIds.length
        ? lineSeries.find(
            (series) =>
              series.regionId === selectedRegionIds[0] && series.indicatorId === selectedIndicator?.id,
          ) ?? null
        : null,
    [lineSeries, selectedRegionIds, selectedIndicator],
  )
  const primaryRegion = useMemo(
    () =>
      selectedRegionIds.length
        ? regions.find((region) => region.id === selectedRegionIds[0]) ?? null
        : null,
    [regions, selectedRegionIds],
  )
  const latestPoint = useMemo(
    () => (primaryRegionSeries ? primaryRegionSeries.points[primaryRegionSeries.points.length - 1] : null),
    [primaryRegionSeries],
  )
  const selectableComparisonYears = useMemo(() => {
    if (!latestPoint || !primaryRegionSeries) {
      return []
    }
    return primaryRegionSeries.points
      .map((point) => point.year)
      .filter((year) => year < latestPoint.year)
      .sort((a, b) => b - a)
  }, [primaryRegionSeries, latestPoint])
  const valueFractionDigits = useMemo(
    () =>
      selectedIndicator?.code.startsWith('AGE_') ||
      selectedIndicator?.code === 'AL_RATE' ||
      selectedIndicator?.code === 'BEV_FOREIGN_SHARE'
        ? 1
        : 0,
    [selectedIndicator],
  )

  const comparisonRows = useMemo(() => {
    if (!selectedIndicator) {
      return []
    }
    const baseSeries = lineSeries.filter((entry) => entry.indicatorId === selectedIndicator.id)
    return baseSeries.map((entry, index) => {
      const currentPoint = entry.points[entry.points.length - 1] ?? null
      const comparePoint =
        comparisonYear !== null
          ? entry.points.find((point) => point.year === comparisonYear) ?? null
          : null

      const changeAbsolute =
        currentPoint && comparePoint ? currentPoint.value - comparePoint.value : null
      const changePercent =
        currentPoint && comparePoint && comparePoint.value !== 0
          ? (changeAbsolute! / comparePoint.value) * 100
          : null

      return {
        name: displayText(entry.regionName),
        currentValue: currentPoint?.value ?? null,
        changeAbsolute,
        changePercent,
        color: getRegionColor(entry.regionName, index),
      }
    })
  }, [lineSeries, comparisonYear, selectedIndicator])

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true)
        const fetchedThemes = await getThemes()
        const fetchedRegions = await getRegions()
        setRegions(fetchedRegions)
        setThemes(fetchedThemes)
        const defaultTheme = fetchedThemes.includes(DEFAULT_THEME)
          ? DEFAULT_THEME
          : (fetchedThemes[0] ?? null)
        if (defaultTheme) {
          setSelectedTheme(defaultTheme)
        }

        const preferredRegionIds = fetchedRegions
          .filter((region) => DEFAULT_REGION_NAMES.includes(region.name))
          .map((region) => region.id)
        if (preferredRegionIds.length) {
          setSelectedRegionIds(preferredRegionIds)
        } else if (fetchedRegions[0]) {
          setSelectedRegionIds([fetchedRegions[0].id])
        }
      } catch {
        setError('Initiale Daten konnten nicht geladen werden.')
      } finally {
        setLoading(false)
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    async function loadThemeIndicators() {
      if (!selectedTheme) {
        setThemeIndicators([])
        setSelectedAreaIds([])
        return
      }
      const rows = await getIndicators(selectedTheme)
      setThemeIndicators(rows)
      setSelectedAreaIds((previous) => {
        const ids = rows.map((indicator) => indicator.id)
        const remaining = previous.filter((id) => ids.includes(id))
        if (remaining.length) {
          return remaining
        }
        const defaultIndicatorCode = selectedTheme ? THEME_DEFAULT_INDICATOR_CODE[selectedTheme] : undefined
        if (defaultIndicatorCode) {
          const defaultIndicatorId = rows.find((indicator) => indicator.code === defaultIndicatorCode)?.id
          if (defaultIndicatorId) {
            return [defaultIndicatorId]
          }
        }
        return ids
      })
    }
    void loadThemeIndicators()
  }, [selectedTheme])

  useEffect(() => {
    if (!regions.length) {
      return
    }
    setSelectedRegionIds((previous) => {
      const regionIds = regions.map((region) => region.id)
      const remaining = previous.filter((id) => regionIds.includes(id))
      return remaining.length ? remaining : regionIds
    })
  }, [regions])

  useEffect(() => {
    async function loadData() {
      if (!selectedRegionIds.length || !selectedIndicators.length) {
        setLineSeries([])
        return
      }

      try {
        setLoading(true)
        setError(null)

        const selectedRegions = regions.filter((region) => selectedRegionIds.includes(region.id))
        const seriesBySelection = await Promise.all(
          selectedRegions.flatMap((region) =>
            selectedIndicators.map(async (indicator) => {
              const values = await getData({
                regionId: region.id,
                indicatorId: indicator.id,
                startYear,
                endYear,
              })
              return {
                regionId: region.id,
                regionName: region.name,
                indicatorId: indicator.id,
                indicatorCode: indicator.code,
                indicatorName: indicator.name,
                points: values,
              }
            }),
          ),
        )

        setLineSeries(seriesBySelection)
      } catch {
        setError('Daten konnten nicht geladen werden. Bitte zuerst ETL ausführen.')
      } finally {
        setLoading(false)
      }
    }

    void loadData()
  }, [selectedRegionIds, selectedIndicators, startYear, endYear, regions])

  useEffect(() => {
    if (!latestPoint) {
      setComparisonYear(null)
      return
    }
    const defaultComparisonYear = latestPoint.year - 1
    const hasDefault = selectableComparisonYears.includes(defaultComparisonYear)
    const hasSelected =
      comparisonYear !== null && selectableComparisonYears.includes(comparisonYear)

    if (hasSelected) {
      return
    }

    if (hasDefault) {
      setComparisonYear(defaultComparisonYear)
      return
    }

    setComparisonYear(selectableComparisonYears[0] ?? null)
  }, [latestPoint, selectableComparisonYears, comparisonYear])

  if (loading && !regions.length) {
    return <div className="p-6 text-sm text-gray-600">Lade Dashboard...</div>
  }

  return (
    <Layout
      activePage="dashboard"
      sidebar={
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">Regionen</label>
              <div className="flex gap-2">
                <button
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700"
                  onClick={() => setSelectedRegionIds(regions.map((region) => region.id))}
                  type="button"
                >
                  Alle
                </button>
                <button
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700"
                  onClick={() => setSelectedRegionIds([])}
                  type="button"
                >
                  Keine
                </button>
              </div>
            </div>
            <div className="max-h-52 space-y-2 overflow-y-auto rounded-md border border-gray-200 p-2">
              {regions.map((region) => (
                <label key={region.id} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedRegionIds.includes(region.id)}
                    onChange={(event) => {
                      if (event.target.checked) {
                        setSelectedRegionIds((previous) =>
                          previous.includes(region.id) ? previous : [...previous, region.id],
                        )
                      } else {
                        setSelectedRegionIds((previous) => previous.filter((id) => id !== region.id))
                      }
                    }}
                  />
                  <span>{displayText(region.name)}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              Ausgewählt: {selectedRegionIds.length} von {regions.length}
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Thema</label>
            <select
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={selectedTheme ?? ''}
              onChange={(event) => setSelectedTheme(event.target.value)}
            >
              {themes.map((theme) => (
                <option key={theme} value={theme}>
                  {displayText(theme)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">Bereiche</label>
              <div className="flex gap-2">
                <button
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700"
                  onClick={() => setSelectedAreaIds(themeIndicators.map((indicator) => indicator.id))}
                  type="button"
                >
                  Alle
                </button>
                <button
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700"
                  onClick={() => setSelectedAreaIds([])}
                  type="button"
                >
                  Keine
                </button>
              </div>
            </div>
            <div className="max-h-44 space-y-2 overflow-y-auto rounded-md border border-gray-200 p-2">
              {themeIndicators.map((indicator) => (
                <label key={indicator.id} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedAreaIds.includes(indicator.id)}
                    onChange={(event) => {
                      if (event.target.checked) {
                        setSelectedAreaIds((previous) =>
                          previous.includes(indicator.id) ? previous : [...previous, indicator.id],
                        )
                      } else {
                        setSelectedAreaIds((previous) =>
                          previous.filter((id) => id !== indicator.id),
                        )
                      }
                    }}
                  />
                  <span>{displayText(indicator.name)}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              Ausgewählt: {selectedAreaIds.length} von {themeIndicators.length}
            </p>
          </div>

          <TimeRangeFilter
            startYear={startYear}
            endYear={endYear}
            minYear={2014}
            maxYear={LAST_COMPLETE_YEAR}
            onStartYearChange={(year) => setStartYear(Math.min(Math.max(year, 2014), endYear))}
            onEndYearChange={(year) =>
              setEndYear(Math.max(Math.min(year, LAST_COMPLETE_YEAR), startYear))
            }
          />
        </div>
      }
    >
      {!themes.length ? (
        <div className="rounded-md bg-amber-100 p-3 text-sm text-amber-800">
          Noch keine Themen vorhanden. Bitte ETL zuerst auf der Seite
          {' '}
          <a href="/maintenance" className="underline">
            Maintenance
          </a>
          {' '}
          ausführen.
        </div>
      ) : null}
      {error ? <div className="rounded-md bg-red-100 p-3 text-sm text-red-700">{error}</div> : null}

      <div className="grid gap-4 md:grid-cols-2">
        <KpiCard
          title={`Aktuell: ${displayText(selectedTheme ?? 'Thema')}: ${displayText(selectedIndicator?.name ?? 'Bereich')}`}
          value={formatNumber(latestPoint?.value, valueFractionDigits)}
          subtitle={
            latestPoint
              ? `Region: ${displayText(primaryRegion?.name ?? 'N/A')} | Datenstand: ${latestPoint.year}`
              : `Region: ${displayText(primaryRegion?.name ?? 'N/A')} | Kein Datenstand`
          }
        />
        <KpiCard
          title="Datenquelle"
          value={
            <a
              href="https://www.regionalstatistik.de"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 underline"
            >
              regionalstatistik.de
            </a>
          }
          valueClassName="mt-1 text-base font-semibold"
          subtitle={`Tabelle: ${selectedIndicator?.genesis_table ?? 'N/A'}${
            selectedIndicator?.description ? ` | ${displayText(selectedIndicator.description)}` : ''
          }`}
        />
      </div>

      <PopulationLineChart
        title={`${displayText(selectedTheme ?? 'Thema')}: ${displayText(selectedIndicator?.name ?? 'Bereich')}`}
        fractionDigits={valueFractionDigits}
        series={lineSeries.map((entry) => ({
          name: displayText(
            selectedRegionIds.length > 1 && selectedIndicators.length > 1
              ? `${entry.regionName} - ${entry.indicatorName}`
              : selectedIndicators.length > 1
                ? entry.indicatorName
                : entry.regionName,
          ),
          points: entry.points,
        }))}
      />
      <div className="mt-8">
        <ComparisonBarChart
          rows={comparisonRows}
          comparisonYear={comparisonYear}
          comparisonYears={selectableComparisonYears}
          fractionDigits={valueFractionDigits}
          onComparisonYearChange={(year) => setComparisonYear(year)}
        />
      </div>
    </Layout>
  )
}
