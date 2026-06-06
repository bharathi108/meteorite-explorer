export function formatMass(grams: number | null): string {
  if (grams == null) return 'Unknown'
  if (grams >= 1_000_000) return `${(grams / 1_000_000).toFixed(2)} t`
  if (grams >= 1_000) return `${(grams / 1_000).toFixed(2)} kg`
  return `${grams.toFixed(0)} g`
}

export function formatYear(year: number | null): string {
  return year == null ? 'Unknown' : String(year)
}

export function formatCoordinates(lat: number | null, lng: number | null): string {
  if (lat == null || lng == null) return 'Unknown'
  const latDir = lat >= 0 ? 'N' : 'S'
  const lngDir = lng >= 0 ? 'E' : 'W'
  return `${Math.abs(lat).toFixed(2)}°${latDir}, ${Math.abs(lng).toFixed(2)}°${lngDir}`
}

/** Globe dot radius from mass (log scale). */
export function pointSizeFromMass(grams: number | null): number {
  if (grams == null || grams <= 0) return 0.28
  return Math.min(0.55, Math.max(0.22, Math.log10(grams + 1) * 0.09 + 0.22))
}

/** Globe pillar height from mass — fixed base with a tiny log-scaled bump. */
export function pointAltitudeFromMass(grams: number | null): number {
  const base = 0.013
  if (grams == null || grams <= 0) return base
  return Math.min(0.016, base + Math.log10(grams + 1) * 0.0005)
}
