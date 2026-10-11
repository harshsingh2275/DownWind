/**
 * TypeScript API contracts for DownWind (T-053).
 * Sourced directly from backend/src/handlers/api.py and docs/architecture.md Section 5.
 */

export interface City {
  id: string
  name: string
  state: string
  lat: number
  lon: number
  population: number
  source?: string
}

export interface CitiesResponse {
  cities: City[]
  total: number
}

export interface Cluster {
  clusterId: string
  lat: number
  lon: number
  count: number
  totalFrp: number
  maxFrp: number
  firstSeenUtc: string
  lastSeenUtc: string
  windSpeedKmh: number
  windDirDeg: number
}

export interface ClusterStats {
  totalClusters: number
  totalFires: number
  totalFrp: number
  maxFrp: number
  avgWindSpeedKmh: number
}

export interface ClustersResponse {
  day: string
  clusters: Cluster[]
  stats: ClusterStats
  lastUpdatedUtc: string | null
}

export type Severity = 'High' | 'Medium' | 'Low'

export interface Impact {
  cityId: string
  cityName: string
  nClusters: number
  totalFrp: number
  nearestKm: number
  minEtaHours: number
  severity: Severity
  affectedByClusterIds: string[]
}

export interface ImpactStats {
  totalCitiesAffected: number
  highSeverityCount: number
  mediumSeverityCount: number
  lowSeverityCount: number
  maxCityFrp: number
}

export interface ImpactResponse {
  day: string
  impact: Impact[]
  stats: ImpactStats
  lastUpdatedUtc: string | null
}

export interface SubscribeRequest {
  email: string
  cityId: string
}

export interface SubscribeResponse {
  status: 'accepted'
  message: string
  cityId?: string
}

export interface ApiErrorDetail {
  code: string
  message: string
}

export interface ApiErrorResponse {
  error: ApiErrorDetail
}
