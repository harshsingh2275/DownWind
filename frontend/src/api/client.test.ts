import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ApiClientError,
  getCities,
  getClusters,
  getImpact,
  subscribe,
} from './client'

describe('Typed API Client (T-053)', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('getCities fetches /cities and returns parsed cities list (mocked fetch)', async () => {
    const mockData = {
      cities: [
        { id: 'delhi', name: 'Delhi', state: 'Delhi NCR', lat: 28.6139, lon: 77.209, population: 16787941 },
        { id: 'chandigarh', name: 'Chandigarh', state: 'Chandigarh', lat: 30.7333, lon: 76.7794, population: 1055450 },
      ],
      total: 2,
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as unknown as Response)

    const result = await getCities()
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    const [url] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/cities')
    expect(result.cities).toHaveLength(2)
    expect(result.total).toBe(2)
  })

  it('getClusters formats query parameter for day (mocked fetch)', async () => {
    const mockData = {
      day: '2024-11-01',
      clusters: [
        {
          clusterId: 'c1',
          lat: 30.5,
          lon: 75.2,
          count: 10,
          totalFrp: 250.0,
          maxFrp: 50.0,
          firstSeenUtc: '2024-11-01T06:00:00Z',
          lastSeenUtc: '2024-11-01T08:00:00Z',
          windSpeedKmh: 12.0,
          windDirDeg: 310.0,
        },
      ],
      stats: {
        totalClusters: 1,
        totalFires: 10,
        totalFrp: 250.0,
        maxFrp: 50.0,
        avgWindSpeedKmh: 12.0,
      },
      lastUpdatedUtc: '2024-11-01T08:00:00Z',
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as unknown as Response)

    const result = await getClusters({ day: '2024-11-01' })
    const [url] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/clusters?day=2024-11-01')
    expect(result.clusters[0].clusterId).toBe('c1')
    expect(result.stats.totalClusters).toBe(1)
  })

  it('getClusters formats query parameter for window (mocked fetch)', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ day: '2024-11-01', clusters: [], stats: {}, lastUpdatedUtc: null }),
    } as unknown as Response)

    await getClusters({ window: '24h' })
    const [url] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/clusters?window=24h')
  })

  it('getImpact returns city-level smoke impact and summary stats (mocked fetch)', async () => {
    const mockData = {
      day: '2024-11-01',
      impact: [
        {
          cityId: 'delhi',
          cityName: 'Delhi',
          nClusters: 15,
          totalFrp: 650.0,
          nearestKm: 35.0,
          minEtaHours: 2.5,
          severity: 'High',
          affectedByClusterIds: ['c1', 'c2'],
        },
      ],
      stats: {
        totalCitiesAffected: 1,
        highSeverityCount: 1,
        mediumSeverityCount: 0,
        lowSeverityCount: 0,
        maxCityFrp: 650.0,
      },
      lastUpdatedUtc: '2024-11-01T10:00:00Z',
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as unknown as Response)

    const result = await getImpact({ day: '2024-11-01' })
    expect(result.impact[0].cityId).toBe('delhi')
    expect(result.impact[0].severity).toBe('High')
    expect(result.stats.highSeverityCount).toBe(1)
  })

  it('subscribe sends POST with JSON payload and returns 202 accepted (mocked fetch)', async () => {
    const mockResponse = {
      status: 'accepted',
      message: 'If the email address is valid, a confirmation link has been sent.',
      cityId: 'delhi',
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => mockResponse,
    } as unknown as Response)

    const result = await subscribe({ email: 'citizen@example.com', cityId: 'delhi' })
    const [url, init] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/subscribe')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({
      email: 'citizen@example.com',
      cityId: 'delhi',
    })
    expect(result.status).toBe('accepted')
  })

  it('throws ApiClientError with code and message on 400 error response (mocked fetch)', async () => {
    const errorBody = {
      error: {
        code: 'BAD_REQUEST',
        message: 'Invalid calendar date provided for day.',
      },
    }

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => errorBody,
    } as unknown as Response)

    await expect(getClusters({ day: 'invalid-date' })).rejects.toThrow(ApiClientError)

    try {
      await getClusters({ day: 'invalid-date' })
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(400)
      expect(apiErr.code).toBe('BAD_REQUEST')
      expect(apiErr.message).toBe('Invalid calendar date provided for day.')
    }
  })

  it('handles non-JSON error responses gracefully (mocked fetch)', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('Not JSON')
      },
    } as unknown as Response)

    try {
      await getCities()
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(502)
      expect(apiErr.code).toBe('HTTP_ERROR')
      expect(apiErr.message).toContain('502')
    }
  })

  it('handles network failure with readable error (mocked fetch)', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Connection refused'))

    try {
      await getCities()
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(0)
      expect(apiErr.code).toBe('NETWORK_ERROR')
      expect(apiErr.message).toContain('Failed to connect to DownWind API')
    }
  })
})
