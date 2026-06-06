import type { GlobePoint } from '../types/meteorite'

export const MAX_RENDER_POINTS = 1200
export const MAX_FETCH_VIEWPORT = 2500
export const MAX_FETCH_GLOBAL = 3500

/** Evenly sample points for WebGL rendering while keeping the selected meteorite. */
export function sampleForRender(
  points: GlobePoint[],
  maxCount: number,
  selectedId: number | null,
): GlobePoint[] {
  if (points.length <= maxCount) return points

  const stride = Math.ceil(points.length / maxCount)
  const sampled: GlobePoint[] = []

  for (let i = 0; i < points.length && sampled.length < maxCount; i += stride) {
    sampled.push(points[i])
  }

  if (selectedId != null) {
    const selected = points.find((point) => point.id === selectedId)
    if (selected && !sampled.some((point) => point.id === selectedId)) {
      sampled[sampled.length - 1] = selected
    }
  }

  return sampled
}

export function fetchLimitForViewport(useViewportFilter: boolean): number {
  return useViewportFilter ? MAX_FETCH_VIEWPORT : MAX_FETCH_GLOBAL
}
