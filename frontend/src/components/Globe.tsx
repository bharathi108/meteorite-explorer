import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import GlobeGL, { type GlobeMethods } from 'react-globe.gl'
import type { GlobePoint, GlobePointOfView, Meteorite } from '../types/meteorite'
import { MAX_RENDER_POINTS, sampleForRender } from '../utils/globe'
import { pointAltitudeFromMass, pointSizeFromMass } from '../utils/format'

interface MeteoriteGlobeProps {
  meteorites: Meteorite[]
  selectedId: number | null
  onSelect: (meteorite: Meteorite) => void
  onViewportChange: (pov: GlobePointOfView) => void
}

const EARTH_TEXTURE =
  'https://unpkg.com/three-globe/example/img/earth-night.jpg'
const BUMP_TEXTURE =
  'https://unpkg.com/three-globe/example/img/earth-topology.png'

const INITIAL_POV: GlobePointOfView = { lat: 25, lng: 10, altitude: 2.2 }
const SELECTED_POINT_RADIUS = 0.58
const SELECTED_ALTITUDE_BONUS = 0.001

export default function MeteoriteGlobe({
  meteorites,
  selectedId,
  onSelect,
  onViewportChange,
}: MeteoriteGlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const globeRef = useRef<GlobeMethods | undefined>(undefined)
  const onViewportChangeRef = useRef(onViewportChange)
  const onSelectRef = useRef(onSelect)
  const [globeReady, setGlobeReady] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const lastSelectedIdRef = useRef<number | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const updateSize = () => {
      const { width, height } = container.getBoundingClientRect()
      setDimensions({
        width: Math.round(width),
        height: Math.round(height),
      })
    }

    updateSize()
    const observer = new ResizeObserver(updateSize)
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    onViewportChangeRef.current = onViewportChange
    onSelectRef.current = onSelect
  }, [onViewportChange, onSelect])

  const allPoints = useMemo<GlobePoint[]>(
    () =>
      meteorites
        .filter((m) => m.latitude != null && m.longitude != null)
        .map((m) => ({
          ...m,
          lat: m.latitude as number,
          lng: m.longitude as number,
          size: pointSizeFromMass(m.mass_grams),
          altitude: pointAltitudeFromMass(m.mass_grams),
        })),
    [meteorites],
  )

  const renderPoints = useMemo(() => {
    const sampled = sampleForRender(allPoints, MAX_RENDER_POINTS, selectedId)
    return sampled.map((point) => ({
      ...point,
      size: point.id === selectedId ? SELECTED_POINT_RADIUS : point.size,
      altitude:
        point.id === selectedId
          ? point.altitude + SELECTED_ALTITUDE_BONUS
          : point.altitude,
    }))
  }, [allPoints, selectedId])

  const emitViewport = useCallback((globe: GlobeMethods) => {
    const pov = globe.pointOfView()
    onViewportChangeRef.current({
      lat: pov.lat ?? INITIAL_POV.lat,
      lng: pov.lng ?? INITIAL_POV.lng,
      altitude: pov.altitude ?? INITIAL_POV.altitude,
    })
  }, [])

  const handleGlobeReady = useCallback(() => {
    setGlobeReady(true)
  }, [])

  useEffect(() => {
    if (!globeReady) return
    const globe = globeRef.current
    if (!globe) return

    globe.pointOfView(INITIAL_POV, 0)

    const handleEnd = () => emitViewport(globe)
    const controls = globe.controls()
    controls?.addEventListener('end', handleEnd)
    emitViewport(globe)

    return () => {
      controls?.removeEventListener('end', handleEnd)
    }
  }, [globeReady, emitViewport])

  useEffect(() => {
    if (selectedId == null) {
      lastSelectedIdRef.current = null
      return
    }
    if (lastSelectedIdRef.current === selectedId) return

    const selected = allPoints.find((point) => point.id === selectedId)
    if (!selected) return

    lastSelectedIdRef.current = selectedId
    globeRef.current?.pointOfView(
      { lat: selected.lat, lng: selected.lng, altitude: 1.4 },
      800,
    )
  }, [selectedId, allPoints])

  const pointColor = useCallback(
    (point: object) =>
      (point as GlobePoint).id === selectedId ? '#ffb347' : '#ff6b4a',
    [selectedId],
  )

  const pointLabel = useCallback((point: object) => {
    const meteorite = point as GlobePoint
    const recclass = meteorite.recclass ?? 'Unknown class'
    const fall = meteorite.fall ?? 'Unknown fall'
    const year =
      meteorite.year != null ? ` · ${meteorite.year}` : ''
    return `<div class="globe-tooltip"><strong>${meteorite.name}</strong><br/><span class="globe-tooltip-meta">${recclass} · ${fall}${year}</span></div>`
  }, [])

  const handlePointClick = useCallback((point: object) => {
    onSelectRef.current(point as GlobePoint)
  }, [])

  const handlePointHover = useCallback((point: object | null) => {
    document.body.style.cursor = point ? 'pointer' : ''
  }, [])

  return (
    <div className="globe-container" ref={containerRef}>
      {dimensions.width > 0 && dimensions.height > 0 && (
        <GlobeGL
          ref={globeRef}
          width={dimensions.width}
          height={dimensions.height}
          onGlobeReady={handleGlobeReady}
          globeImageUrl={EARTH_TEXTURE}
          bumpImageUrl={BUMP_TEXTURE}
          backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
          pointsData={renderPoints}
          pointsMerge={false}
          pointResolution={8}
          pointLat="lat"
          pointLng="lng"
          pointAltitude="altitude"
          pointRadius="size"
          pointColor={pointColor}
          pointLabel={pointLabel}
          onPointClick={handlePointClick}
          onPointHover={handlePointHover}
          atmosphereColor="#3a7bd5"
          atmosphereAltitude={0.15}
        />
      )}
    </div>
  )
}
