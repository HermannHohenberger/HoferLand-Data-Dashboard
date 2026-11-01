import { useEffect, useMemo, useState } from 'react'
import { getEtlAreas, runEtlSequential } from '../api/client'
import { Layout } from '../components/Layout'
import type { EtlAreaResult } from '../types'
import { displayText } from '../utils/displayText'

const AREA_LABELS: Record<string, string> = {
  bevoelkerung_gesamt: 'Bevölkerung gesamt',
  auslaender: 'Ausländer',
  durchschnittsalter: 'Durchschnittsalter (gesamt/deutsch/ausländer)',
  wanderung_kreisgrenzen: 'Zu- und Fortzüge über Kreisgrenzen',
  arbeitslose_gesamt: 'Arbeitslose gesamt',
  arbeitslose_auslaender: 'Arbeitslose Ausländer',
  langzeitarbeitslose: 'Langzeitarbeitslose',
  arbeitslosenquote: 'Arbeitslosenquote',
  derived: 'Berechnete Kennzahlen',
}

function formatAreaName(area: string): string {
  return AREA_LABELS[area] ?? area.replaceAll('_', ' ')
}

function formatAreaStatus(status?: string): string {
  if (status === 'error') return 'Fehler'
  if (status === 'empty') return 'Keine Daten'
  return 'OK'
}

export function Maintenance() {
  const currentYear = new Date().getFullYear()
  const defaultStartYear = Math.max(2014, currentYear - 2)
  const [areas, setAreas] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [results, setResults] = useState<EtlAreaResult[]>([])
  const [requestedAreas, setRequestedAreas] = useState<string[]>([])
  const [lastRunAt, setLastRunAt] = useState<string | null>(null)
  const [startYear, setStartYear] = useState(defaultStartYear)

  useEffect(() => {
    async function loadAreas() {
      try {
        const values = await getEtlAreas()
        setAreas(values)
      } catch {
        setError('ETL-Bereiche konnten nicht geladen werden.')
      }
    }
    void loadAreas()
  }, [])

  const totalTouched = useMemo(
    () => results.reduce((sum, item) => sum + item.inserted_or_updated, 0),
    [results],
  )

  async function runAreas(selectedAreas?: string[]) {
    const targets = selectedAreas?.length ? selectedAreas : areas
    setRequestedAreas(targets)
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await runEtlSequential(selectedAreas, startYear)
      setResults(response.results)
      setLastRunAt(new Date().toLocaleString('de-DE'))
      setSuccess(
        `ETL abgeschlossen für ${targets.map(formatAreaName).join(', ')} (ab ${startYear}). Insgesamt aktualisiert/neu geschrieben: ${response.total_inserted_or_updated}.`,
      )
    } catch {
      setError('ETL-Lauf fehlgeschlagen. Bitte Backend-Logs prüfen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout
      activePage="maintenance"
      sidebar={
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-800">ETL-Steuerung</h2>
          <p className="text-xs text-gray-600">
            Führe ETL-Bereiche manuell und nacheinander aus.
          </p>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-gray-500">
              Startjahr ETL
            </label>
            <input
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              type="number"
              min={2014}
              max={currentYear}
              value={startYear}
              onChange={(event) =>
                setStartYear(Math.max(2014, Math.min(currentYear, Number(event.target.value) || 2014)))
              }
            />
          </div>
          <button
            type="button"
            disabled={loading}
            onClick={() => void runAreas()}
            className="w-full rounded-md border border-blue-600 bg-white px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-600 hover:text-white active:bg-blue-100 active:text-blue-800 disabled:opacity-50"
          >
            Alle Bereiche nacheinander starten
          </button>
          <div className="space-y-2">
            {areas.map((area) => (
              <button
                key={area}
                type="button"
                disabled={loading}
                onClick={() => void runAreas([area])}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:border-blue-600 hover:bg-blue-600 hover:text-white active:bg-blue-100 active:text-blue-800 disabled:opacity-50"
              >
                {formatAreaName(area)}
              </button>
            ))}
          </div>
        </div>
      }
    >
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Maintenance</h2>
        <p className="mt-1 text-sm text-gray-600">
          Hier kannst du den ETL manuell ausführen. Die Bereiche werden sequentiell verarbeitet.
        </p>
        {loading && requestedAreas.length ? (
          <p className="mt-2 text-sm text-blue-700">
            Lauf gestartet für: {requestedAreas.map(formatAreaName).join(', ')} (ab {startYear})
          </p>
        ) : null}
      </div>

      {error ? <div className="rounded-md bg-red-100 p-3 text-sm text-red-700">{error}</div> : null}
      {success ? <div className="rounded-md bg-green-100 p-3 text-sm text-green-700">{success}</div> : null}

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-800">Letztes ETL-Ergebnis</h3>
        {!results.length ? (
          <p className="mt-2 text-sm text-gray-500">Noch kein Lauf gestartet.</p>
        ) : (
          <div className="mt-3 space-y-2">
            <div className="rounded border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
              <div>
                Angefordert: {requestedAreas.map(formatAreaName).join(', ')} (ab {startYear})
              </div>
              {lastRunAt ? <div>Letzter Lauf: {lastRunAt}</div> : null}
            </div>
            {results.map((item) => (
              <div
                key={item.area}
                className="rounded border border-gray-200 px-3 py-2 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span>{formatAreaName(item.area)}</span>
                  <span className="font-medium">{item.inserted_or_updated}</span>
                </div>
                <div className="mt-1 text-xs text-gray-600">
                  Status: {formatAreaStatus(item.status)}
                  {item.message ? ` | ${displayText(item.message)}` : ''}
                </div>
              </div>
            ))}
            <div className="mt-2 flex items-center justify-between border-t border-gray-200 pt-2 text-sm font-semibold">
              <span>Gesamt</span>
              <span>{totalTouched}</span>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
