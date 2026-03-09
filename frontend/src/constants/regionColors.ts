const LINE_COLORS = [
  '#2563eb',
  '#dc2626',
  '#16a34a',
  '#d97706',
  '#9333ea',
  '#0891b2',
  '#be123c',
  '#4f46e5',
  '#0f766e',
  '#a16207',
  '#334155',
]

const REGION_COLOR_ORDER: string[] = [
  'Bayern',
  'Oberfranken, Regierungsbezirk',
  'Bayreuth, kreisfreie Stadt',
  'Hof, kreisfreie Stadt',
  'Bayreuth, Landkreis',
  'Hof, Landkreis',
  'Kronach, Landkreis',
  'Kulmbach, Landkreis',
  'Wunsiedel i.Fichtelgebirge, Landkreis',
  'Vogtlandkreis',
  'Saale-Orla-Kreis',
]

const REGION_COLOR_MAP = Object.fromEntries(
  REGION_COLOR_ORDER.map((name, index) => [name, LINE_COLORS[index % LINE_COLORS.length]]),
) as Record<string, string>

export function getRegionColor(regionName: string, fallbackIndex = 0): string {
  return REGION_COLOR_MAP[regionName] ?? LINE_COLORS[fallbackIndex % LINE_COLORS.length]
}
