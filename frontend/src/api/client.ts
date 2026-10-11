/**
 * Typed HTTP API client for DownWind (T-053).
 * Consumes endpoints deployed per docs/architecture.md Section 5.
 */

import type {
  ApiErrorResponse,
  CitiesResponse,
  ClustersResponse,
  ImpactResponse,
  SubscribeRequest,
  SubscribeResponse,
} from '../types/api'

export class ApiClientError extends Error {
  public readonly status: number
  public readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
  }
}

export function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (typeof envUrl === 'string' && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '')
  }
  return ''
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const url = `${baseUrl}${cleanEndpoint}`

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    })
  } catch (err) {
    throw new ApiClientError(
      0,
      'NETWORK_ERROR',
      `Failed to connect to DownWind API: ${err instanceof Error ? err.message : String(err)}`,
    )
  }

  // Handle errors
  if (!response.ok) {
    let errorCode = 'HTTP_ERROR'
    let errorMessage = `Request failed with status ${response.status}`

    try {
      const errorJson = (await response.json()) as ApiErrorResponse
      if (errorJson && errorJson.error) {
        errorCode = errorJson.error.code || errorCode
        errorMessage = errorJson.error.message || errorMessage
      }
    } catch {
      // Body was not JSON; use default status message
    }

    throw new ApiClientError(response.status, errorCode, errorMessage)
  }

  return (await response.json()) as T
}

/**
 * Fetch starter list of monitored urban centers.
 */
export async function getCities(): Promise<CitiesResponse> {
  return request<CitiesResponse>('/cities')
}

/**
 * Fetch fire clusters with optional date or rolling window filter.
 */
export async function getClusters(params?: {
  day?: string
  window?: string
}): Promise<ClustersResponse> {
  const query = new URLSearchParams()
  if (params?.day) {
    query.set('day', params.day)
  }
  if (params?.window) {
    query.set('window', params.window)
  }

  const qs = query.toString()
  const endpoint = qs ? `/clusters?${qs}` : '/clusters'
  return request<ClustersResponse>(endpoint)
}

/**
 * Fetch city-level smoke impact records and summary statistics.
 */
export async function getImpact(params?: {
  day?: string
  window?: string
}): Promise<ImpactResponse> {
  const query = new URLSearchParams()
  if (params?.day) {
    query.set('day', params.day)
  }
  if (params?.window) {
    query.set('window', params.window)
  }

  const qs = query.toString()
  const endpoint = qs ? `/impact?${qs}` : '/impact'
  return request<ImpactResponse>(endpoint)
}

/**
 * Subscribe an email address to a city's smoke alerts (double opt-in).
 */
export async function subscribe(data: SubscribeRequest): Promise<SubscribeResponse> {
  return request<SubscribeResponse>('/subscribe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export const apiClient = {
  getCities,
  getClusters,
  getImpact,
  subscribe,
}

