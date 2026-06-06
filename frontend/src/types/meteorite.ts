export interface Meteorite {
  id: number
  name: string
  nametype: string
  recclass: string | null
  mass_grams: number | null
  fall: string | null
  year: number | null
  latitude: number | null
  longitude: number | null
}

export interface MeteoriteListResponse {
  items: Meteorite[]
  total: number
  limit: number
  offset: number
}

export interface AIExplanationResponse {
  meteorite_id: number
  explanation: string
  cached: boolean
  model: string
  prompt_version: string
  created_at: string | null
}

export type FallFilter = '' | 'Fell' | 'Found'

export interface MeteoriteFilters {
  search: string
  recclass: string
  fall: FallFilter
  minYear: string
  maxYear: string
  minMass: string
  maxMass: string
}

export const emptyFilters: MeteoriteFilters = {
  search: '',
  recclass: '',
  fall: '',
  minYear: '',
  maxYear: '',
  minMass: '',
  maxMass: '',
}

export interface GlobePoint extends Meteorite {
  lat: number
  lng: number
  size: number
  altitude: number
}

export type { GlobePointOfView, ViewportBounds } from '../utils/viewport'
