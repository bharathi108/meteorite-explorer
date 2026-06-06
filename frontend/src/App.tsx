import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchMeteorites } from './api/meteorites'
import GlobeInsightCard, { useMeteoriteExplanation } from './components/GlobeInsightCard'
import MeteoriteGlobe from './components/Globe'
import FilterPanel from './components/FilterPanel'
import MeteoriteDetails from './components/MeteoriteDetails'
import type { GlobePointOfView, Meteorite, MeteoriteFilters } from './types/meteorite'
import { emptyFilters } from './types/meteorite'
import { fetchLimitForViewport } from './utils/globe'
import {
  boundsFromPointOfView,
  hasViewportChangedSignificantly,
  isGlobalViewport,
} from './utils/viewport'

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}

const INITIAL_POV: GlobePointOfView = { lat: 25, lng: 10, altitude: 2.2 }

export default function App() {
  const [filters, setFilters] = useState<MeteoriteFilters>(emptyFilters)
  const debouncedFilters = useDebouncedValue(filters, 400)

  const [viewportPov, setViewportPov] = useState<GlobePointOfView>(INITIAL_POV)
  const debouncedViewportPov = useDebouncedValue(viewportPov, 500)

  const viewportBounds = useMemo(
    () => boundsFromPointOfView(debouncedViewportPov),
    [debouncedViewportPov],
  )
  const useViewportFilter = !isGlobalViewport(viewportBounds)

  const [meteorites, setMeteorites] = useState<Meteorite[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Meteorite | null>(null)
  const hasLoadedOnce = useRef(false)

  useEffect(() => {
    let cancelled = false
    if (!hasLoadedOnce.current) setLoading(true)
    else setRefreshing(true)
    setError(null)

    const limit = fetchLimitForViewport(useViewportFilter)

    fetchMeteorites(debouncedFilters, useViewportFilter ? viewportBounds : null, limit)
      .then((response) => {
        if (cancelled) return
        setMeteorites(response.items)
        setTotal(response.total)
        setSelected((current) => {
          if (!current) return null
          return response.items.find((item) => item.id === current.id) ?? null
        })
        hasLoadedOnce.current = true
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (!hasLoadedOnce.current) setMeteorites([])
        setTotal(0)
        setError(err instanceof Error ? err.message : 'Failed to load meteorites.')
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
          setRefreshing(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [debouncedFilters, viewportBounds, useViewportFilter])

  const handleReset = useCallback(() => {
    setFilters(emptyFilters)
    setSelected(null)
  }, [])

  const handleViewportChange = useCallback((pov: GlobePointOfView) => {
    setViewportPov((current) =>
      hasViewportChangedSignificantly(current, pov) ? pov : current,
    )
  }, [])

  const showLimitBanner = !error && total > meteorites.length
  const explanation = useMeteoriteExplanation(selected?.id ?? null)

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <p className="eyebrow">NASA Meteorite Landings</p>
          <h1>Meteorite Explorer</h1>
        </div>
        <p className="header-copy">
          Explore meteorite discoveries on an interactive globe and learn what makes each one scientifically interesting.
        </p>
      </header>

      <main className="app-layout">
        <aside className="sidebar">
          <div className="sidebar-scroll">
            <FilterPanel
              filters={filters}
              onChange={setFilters}
              onReset={handleReset}
              total={total}
              shown={meteorites.length}
              loading={loading}
              refreshing={refreshing}
              viewportScoped={useViewportFilter}
            />
          </div>
          {selected && (
            <div className="sidebar-selection sidebar-selection--active">
              <MeteoriteDetails meteorite={selected} />
            </div>
          )}
        </aside>

        <section className={`globe-stage${refreshing ? ' globe-stage--refreshing' : ''}`}>
          {error && <div className="banner error-banner">{error}</div>}
          {showLimitBanner && (
            <div className="banner info-banner">
              {useViewportFilter
                ? `Showing up to ${meteorites.length.toLocaleString()} of ${total.toLocaleString()} in this view. Zoom in or refine filters.`
                : `Showing up to ${meteorites.length.toLocaleString()} of ${total.toLocaleString()} worldwide. Zoom in to explore by region.`}
            </div>
          )}
          <GlobeInsightCard meteorite={selected} explanation={explanation} />
          <MeteoriteGlobe
            meteorites={meteorites}
            selectedId={selected?.id ?? null}
            onSelect={setSelected}
            onViewportChange={handleViewportChange}
          />
        </section>
      </main>
    </div>
  )
}
