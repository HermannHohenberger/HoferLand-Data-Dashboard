import type { ReactNode } from 'react'

type LayoutProps = {
  sidebar?: ReactNode
  children: ReactNode
  activePage?: 'dashboard' | 'maintenance' | 'ueber' | 'impressum'
}

export function Layout({ sidebar, children, activePage = 'dashboard' }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">HoferLand Data Dashboard</h1>
            <p className="text-sm text-gray-500">Kennzahlen für das HoferLand und angrenzende Regionen</p>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <a
              href="/"
              className={`rounded px-3 py-1 ${
                activePage === 'dashboard'
                  ? 'bg-blue-100 font-medium text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Dashboard
            </a>
            <a
              href="/ueber"
              className={`rounded px-3 py-1 ${
                activePage === 'ueber'
                  ? 'bg-blue-100 font-medium text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Über
            </a>
            <a
              href="/impressum"
              className={`rounded px-3 py-1 ${
                activePage === 'impressum'
                  ? 'bg-blue-100 font-medium text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Impressum
            </a>
          </nav>
        </div>
      </header>
      {sidebar ? (
        <main className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-6 px-4 py-6 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            {sidebar}
          </aside>
          <section className="space-y-6">{children}</section>
        </main>
      ) : (
        <main className="mx-auto w-full max-w-4xl px-4 py-6">
          <section className="space-y-6">{children}</section>
        </main>
      )}
    </div>
  )
}
