import { useEffect, useState } from 'react'
import { fetchExplanation } from '../api/meteorites'
import type { Meteorite } from '../types/meteorite'

export type ExplanationState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; text: string; cached: boolean }
  | { status: 'unavailable'; message: string }

export function useMeteoriteExplanation(meteoriteId: number | null): ExplanationState {
  const [state, setState] = useState<ExplanationState>({ status: 'idle' })

  useEffect(() => {
    if (meteoriteId == null) {
      setState({ status: 'idle' })
      return
    }

    let cancelled = false
    setState({ status: 'loading' })

    fetchExplanation(meteoriteId)
      .then((response) => {
        if (cancelled) return
        setState({
          status: 'success',
          text: response.explanation,
          cached: response.cached,
        })
      })
      .catch(() => {
        if (cancelled) return
        setState({
          status: 'unavailable',
          message: 'Could not generate an explanation right now. Please try again later.',
        })
      })

    return () => {
      cancelled = true
    }
  }, [meteoriteId])

  return state
}

interface GlobeInsightCardProps {
  meteorite: Meteorite | null
  explanation: ExplanationState
}

export default function GlobeInsightCard({
  meteorite,
  explanation,
}: GlobeInsightCardProps) {
  if (!meteorite) return null

  return (
    <aside className="globe-insight" aria-live="polite">
      <header className="globe-insight-header">
        <div>
          <p className="globe-insight-eyebrow">AI insight</p>
          <h2 className="globe-insight-title">{meteorite.name}</h2>
        </div>
        {explanation.status === 'success' && explanation.cached && (
          <span className="badge">Cached</span>
        )}
      </header>

      {explanation.status === 'loading' && (
        <p className="globe-insight-body loading-text">Generating summary…</p>
      )}

      {explanation.status === 'success' && (
        <p className="globe-insight-body ai-text">{explanation.text}</p>
      )}

      {explanation.status === 'unavailable' && (
        <p className="globe-insight-body info-text">{explanation.message}</p>
      )}
    </aside>
  )
}
