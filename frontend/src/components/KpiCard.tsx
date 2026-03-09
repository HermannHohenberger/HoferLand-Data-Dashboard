import type { ReactNode } from 'react'

type KpiCardProps = {
  title: string
  value: ReactNode
  valueClassName?: string
  subtitle?: string
  controls?: ReactNode
}

export function KpiCard({ title, value, valueClassName, subtitle, controls }: KpiCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-gray-500">{title}</p>
        {controls}
      </div>
      <div className={valueClassName ?? 'mt-1 text-2xl font-semibold'}>{value}</div>
      {subtitle ? <p className="mt-2 text-sm text-gray-600">{subtitle}</p> : null}
    </div>
  )
}
