import { useState, useEffect, useCallback } from 'react'
import { Link } from '../router'
import { apiClient, ApiClientError } from '../api/client'
import type { Cluster, ClustersResponse } from '../types/api'
import { ClusterMap } from '../components/ClusterMap'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { ErrorMessage } from '../components/ErrorMessage'
import { SAMPLE_CLUSTERS } from '../fixtures/sampleClusters'

export function HomePage() {
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [stats, setStats] = useState<ClustersResponse['stats'] | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isUsingSampleData, setIsUsingSampleData] = useState(false)

  const fetchClusters = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await apiClient.getClusters()
      setClusters(res.clusters)
      setStats(res.stats)
      setLastUpdated(res.lastUpdatedUtc || null)
      setIsUsingSampleData(false)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to load active satellite telemetry.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let isCancelled = false
    apiClient
      .getClusters()
      .then((res: ClustersResponse) => {
        if (!isCancelled) {
          setClusters(res.clusters)
          setStats(res.stats)
          setLastUpdated(res.lastUpdatedUtc || null)
          setIsUsingSampleData(false)
          setIsLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!isCancelled) {
          if (err instanceof ApiClientError) {
            setError(err.message)
          } else if (err instanceof Error) {
            setError(err.message)
          } else {
            setError('Failed to load active satellite telemetry.')
          }
          setIsLoading(false)
        }
      })

    return () => {
      isCancelled = true
    }
  }, [])

  const loadSampleData = () => {
    setClusters(SAMPLE_CLUSTERS)
    setStats({
      totalClusters: SAMPLE_CLUSTERS.length,
      totalFires: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.count, 0),
      totalFrp: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.totalFrp, 0),
      maxFrp: Math.max(...SAMPLE_CLUSTERS.map((c) => c.maxFrp)),
      avgWindSpeedKmh: 14.0,
    })
    setLastUpdated('Today 06:00 IST (Sample Reference)')
    setIsUsingSampleData(true)
    setError(null)
  }

  return (
    <div className="space-y-12">
      {/* Top Sub-Header Metadata Bar per Stitch Reference */}
      <div className="border-b border-divider pb-3 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-text-muted uppercase tracking-wider">
        <div className="flex items-center gap-2">
          <span>Satellite Fire &amp; Smoke Trajectory</span>
          <span className="text-divider">•</span>
          <span>Punjab &amp; Haryana</span>
        </div>
        <div>
          <span>Updated: {lastUpdated ? lastUpdated : 'Today 06:00 IST'}</span>
          {isUsingSampleData && (
            <span className="ml-2 px-1.5 py-0.5 border border-neutral-low text-neutral-low text-[10px]">
              Sample Preview
            </span>
          )}
        </div>
      </div>

      {/* Hero Section: Asymmetric 2-Column Grid on Desktop, Stacked on Mobile */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
        {/* Left Column: Eyebrow, Headline, Explanation, Actions, Source Attribution */}
        <div className="flex flex-col justify-between">
          <div>
            <span className="font-mono text-[12px] text-text-muted uppercase tracking-wider block mb-3">
              Monitoring Overview
            </span>

            <h1 className="text-[32px] sm:text-[38px] lg:text-[44px] font-semibold text-text leading-[1.12] tracking-tight mb-4">
              Fire detections across Punjab and Haryana, and where the smoke may go next
            </h1>

            <p className="text-body text-text-muted mb-8 max-w-[54ch] leading-[1.6]">
              Near real-time thermal anomaly data tracked alongside atmospheric wind models to map downwind particulate spread across northern India.
            </p>

            <div className="flex flex-wrap items-center gap-4 sm:gap-6 mb-8">
              <Link
                href="/map"
                className="w-full sm:w-auto bg-accent hover:bg-accent-hover text-white px-6 py-3 min-h-[44px] font-sans text-small font-medium no-underline inline-flex items-center justify-center border-0 cursor-pointer transition-colors"
              >
                See the live map
              </Link>
              <Link
                href="/method"
                className="text-accent hover:text-accent-hover underline text-small font-medium"
              >
                How the estimate works
              </Link>
            </div>
          </div>

          <div className="pt-4 border-t border-divider mt-4">
            <p className="font-mono text-[11px] text-text-muted leading-[1.6] m-0">
              Source layers: MODIS / VIIRS 375m active fire telemetry. Atmospheric dispersion model computed hourly at 10m surface layer wind vectors.
            </p>
          </div>
        </div>

        {/* Right Column: Live Map Container matching Stitch Reference */}
        <div className="border border-divider bg-surface p-4 flex flex-col">
          <div className="flex justify-between items-center border-b border-divider pb-2 mb-3 text-[11px] font-mono text-text-muted">
            <span>MAP LAYOUT REFERENCE • 29.5°N - 32.0°N</span>
            <span>Scale 1:750,000</span>
          </div>

          {/* Map Async States */}
          {isLoading && (
            <LoadingSkeleton height="h-[380px]" lines={5} />
          )}

          {!isLoading && error && (
            <div className="space-y-4">
              <ErrorMessage
                title="Telemetry Unavailable"
                message={`${error}. Live satellite fire coordinates could not be loaded.`}
                onRetry={fetchClusters}
              />
              <div className="border border-divider bg-bg p-3 flex flex-wrap items-center justify-between gap-3">
                <span className="text-[12px] text-text-muted">
                  Inspect layout with approved sample telemetry fixtures:
                </span>
                <button
                  type="button"
                  onClick={loadSampleData}
                  className="bg-accent hover:bg-accent-hover text-white text-small px-3 py-1.5 border-0 font-medium cursor-pointer"
                >
                  Load Sample Fixtures
                </button>
              </div>
            </div>
          )}

          {!isLoading && !error && (
            <>
              {/* Interactive React-Leaflet Map */}
              <ClusterMap
                clusters={clusters}
                height="380px"
              />

              {/* Bottom Map Metadata & Legend */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-text-muted pt-3 mt-3 border-t border-divider">
                <div className="flex items-center flex-wrap gap-3">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 bg-accent inline-block border border-[#78270E]" />
                    <span className="text-text font-medium">High radiative power</span> (&ge;500 MW)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 bg-accent-mid inline-block border border-[#7B3116]" />
                    <span className="text-text font-medium">Medium</span> (&ge;150 MW)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 border-2 border-neutral-low bg-bg inline-block" />
                    <span>Low</span>
                  </span>
                </div>
                <span className="font-mono">
                  Projection: WGS 84 / UTM
                </span>
              </div>
            </>
          )}
        </div>
      </section>

      {/* Summary Stats Bar: Computed from Real API Data per Stitch Design */}
      <section className="border border-divider bg-surface">
        {isLoading && (
          <div className="p-4">
            <LoadingSkeleton height="h-16" lines={2} />
          </div>
        )}

        {!isLoading && error && (
          <div className="p-4 text-center text-text-muted text-small">
            Stats offline. Retry connection to load live metrics.
          </div>
        )}

        {!isLoading && !error && stats && (
          <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-divider">
            <div className="p-5 flex flex-col justify-between">
              <span className="font-mono text-[28px] sm:text-[32px] font-semibold text-text tracking-tight block">
                {stats.totalFires.toLocaleString()}
              </span>
              <span className="text-[12px] text-text-muted mt-1 font-sans">
                Active fire detections (24h)
              </span>
            </div>

            <div className="p-5 flex flex-col justify-between">
              <span className="font-mono text-[28px] sm:text-[32px] font-semibold text-text tracking-tight block">
                {stats.avgWindSpeedKmh.toFixed(0)} km/h
              </span>
              <span className="text-[12px] text-text-muted mt-1 font-sans">
                Prevailing NW wind vector
              </span>
            </div>

            <div className="p-5 flex flex-col justify-between">
              <span className="font-mono text-[28px] sm:text-[32px] font-semibold text-accent tracking-tight block">
                {stats.totalFrp.toFixed(0)} MW
              </span>
              <span className="text-[12px] text-text-muted mt-1 font-sans">
                Total radiative power
              </span>
            </div>
          </div>
        )}
      </section>

      {/* How the Estimate Works (Numbered vertical list per design.md §8) */}
      <section className="border-t border-divider pt-12 max-w-[64ch]">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text mb-6">
          How the estimate works
        </h2>

        <ol className="list-none p-0 m-0 space-y-6">
          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              01 • Thermal anomaly detection
            </span>
            <p className="text-body text-text-muted m-0">
              NASA FIRMS satellites (VIIRS 375m sensor) detect active heat signatures across the agricultural corridor of Punjab and Haryana in near real-time.
            </p>
          </li>

          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              02 • Spatial clustering &amp; intensity
            </span>
            <p className="text-body text-text-muted m-0">
              Nearby fire detections within 0.05° grid cells are clustered into aggregated burn centers with fire radiative power (FRP) weighted centroids.
            </p>
          </li>

          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              03 • Atmospheric wind vector modeling
            </span>
            <p className="text-body text-text-muted m-0">
              High-resolution hourly surface wind data from Open-Meteo determines downwind smoke trajectory corridors, arrival time estimates (ETA), and city risk severity.
            </p>
          </li>
        </ol>
      </section>
    </div>
  )
}
