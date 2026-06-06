import type {
  AIExplanationResponse,
  Meteorite,
  MeteoriteFilters,
  MeteoriteListResponse,
  ViewportBounds,
} from '../types/meteorite'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((item: { msg?: string }) => item.msg ?? '').join(', ')
      }
    } catch {
      // use statusText
    }
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}

function buildFilterParams(
  filters: MeteoriteFilters,
  viewport: ViewportBounds | null,
  limit = 10000,
  offset = 0,
): string {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  params.set('offset', String(offset))

  if (filters.search.trim()) params.set('search', filters.search.trim())
  if (filters.recclass.trim()) params.set('recclass', filters.recclass.trim())
  if (filters.fall) params.set('fall', filters.fall)
  if (filters.minYear) params.set('min_year', filters.minYear)
  if (filters.maxYear) params.set('max_year', filters.maxYear)
  if (filters.minMass) params.set('min_mass', filters.minMass)
  if (filters.maxMass) params.set('max_mass', filters.maxMass)

  if (viewport) {
    params.set('min_lat', viewport.min_lat.toFixed(4))
    params.set('max_lat', viewport.max_lat.toFixed(4))
    params.set('min_lng', viewport.min_lng.toFixed(4))
    params.set('max_lng', viewport.max_lng.toFixed(4))
  }

  return params.toString()
}

export async function fetchMeteorites(
  filters: MeteoriteFilters,
  viewport: ViewportBounds | null = null,
  limit = 10000,
  offset = 0,
): Promise<MeteoriteListResponse> {
  const query = buildFilterParams(filters, viewport, limit, offset)
  return request<MeteoriteListResponse>(`/meteorites?${query}`)
}

export async function fetchRecclasses(): Promise<string[]> {
  return request<string[]>('/meteorites/recclasses')
}

export async function fetchMeteorite(id: number): Promise<Meteorite> {
  return request<Meteorite>(`/meteorites/${id}`)
}

export async function fetchExplanation(id: number): Promise<AIExplanationResponse> {
  return request<AIExplanationResponse>(`/meteorites/${id}/explanation`, {
    method: 'POST',
  })
}

export { ApiError }
