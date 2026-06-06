export interface GlobePointOfView {
  lat: number
  lng: number
  altitude: number
}

export interface ViewportBounds {
  min_lat: number
  max_lat: number
  min_lng: number
  max_lng: number
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function normalizeLng(lng: number): number {
  let normalized = lng
  while (normalized > 180) normalized -= 360
  while (normalized < -180) normalized += 360
  return normalized
}

/** Approximate lat/lng bounds visible from the current globe camera. */
export function boundsFromPointOfView(pov: GlobePointOfView): ViewportBounds {
  // Higher altitude = camera farther away = larger visible area.
  const latHalfSpan = clamp((22 * pov.altitude) + 8, 12, 85)
  const lngHalfSpan = clamp((34 * pov.altitude) + 12, 18, 175)

  const min_lat = clamp(pov.lat - latHalfSpan, -90, 90)
  const max_lat = clamp(pov.lat + latHalfSpan, -90, 90)

  const min_lng = normalizeLng(pov.lng - lngHalfSpan)
  const max_lng = normalizeLng(pov.lng + lngHalfSpan)

  return { min_lat, max_lat, min_lng, max_lng }
}

export function isGlobalViewport(bounds: ViewportBounds): boolean {
  const latSpan = bounds.max_lat - bounds.min_lat
  const lngSpan =
    bounds.min_lng <= bounds.max_lng
      ? bounds.max_lng - bounds.min_lng
      : 360 - bounds.min_lng + bounds.max_lng
  return latSpan >= 170 && lngSpan >= 340
}

/** Skip refetch/re-render when the camera barely moved. */
export function hasViewportChangedSignificantly(
  prev: GlobePointOfView,
  next: GlobePointOfView,
): boolean {
  const latDelta = Math.abs(prev.lat - next.lat)
  const lngDelta = Math.min(
    Math.abs(prev.lng - next.lng),
    360 - Math.abs(prev.lng - next.lng),
  )
  const altDelta = Math.abs(prev.altitude - next.altitude)

  if (altDelta >= 0.15) return true
  if (latDelta >= 4 || lngDelta >= 6) return true
  return false
}
