import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Layout } from '../components/Layout'

type MarkdownStaticPageProps = {
  title: string
  markdownPath: string
  activePage: 'ueber' | 'impressum'
}

function renderInlineBold(text: string): ReactNode[] {
  return text.split(/(\*\*.*?\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return <span key={index}>{part}</span>
  })
}

function renderMarkdownSimple(content: string): ReactNode[] {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const elements: ReactNode[] = []
  let bulletItems: string[] = []

  const flushBullets = (keySeed: number) => {
    if (!bulletItems.length) {
      return
    }
    elements.push(
      <ul key={`list-${keySeed}`} className="list-disc space-y-1 pl-5">
        {bulletItems.map((item, index) => (
          <li key={index}>{renderInlineBold(item)}</li>
        ))}
      </ul>,
    )
    bulletItems = []
  }

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim()
    if (line.startsWith('- ')) {
      bulletItems.push(line.slice(2).trim())
      return
    }

    flushBullets(index)
    if (!line) {
      elements.push(<div key={`spacer-${index}`} className="h-2" />)
      return
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={`h1-${index}`} className="text-2xl font-semibold text-gray-900">
          {line.slice(2).trim()}
        </h2>,
      )
      return
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={`h2-${index}`} className="text-lg font-semibold text-gray-900">
          {line.slice(3).trim()}
        </h3>,
      )
      return
    }
    elements.push(
      <p key={`p-${index}`} className="leading-7 text-gray-700">
        {renderInlineBold(line)}
      </p>,
    )
  })

  flushBullets(lines.length)
  return elements
}

export function MarkdownStaticPage({ title, markdownPath, activePage }: MarkdownStaticPageProps) {
  const [content, setContent] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadMarkdown() {
      try {
        const response = await fetch(markdownPath)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const text = await response.text()
        if (!cancelled) {
          setContent(text)
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setContent('')
          setError('Inhalt konnte nicht geladen werden.')
        }
      }
    }
    void loadMarkdown()
    return () => {
      cancelled = true
    }
  }, [markdownPath])

  const rendered = useMemo(() => renderMarkdownSimple(content), [content])

  return (
    <Layout activePage={activePage}>
      <article className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="mb-4 text-2xl font-semibold text-gray-900">{title}</h1>
        {error ? <p className="text-sm text-red-700">{error}</p> : <div className="space-y-1">{rendered}</div>}
      </article>
    </Layout>
  )
}
