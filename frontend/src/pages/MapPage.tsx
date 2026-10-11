import { useState, useEffect, useCallback } from 'react'
import { apiClient, ApiClientError } from '../api/client'
import type { Cluster, ClustersResponse } from '../types/api'
import { ClusterMap, ClusterCompanionTable } from '../components/ClusterMap'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { ErrorMessage } from '../components/ErrorMessage'
import { EmptyState } from '../components/EmptyState'
import { SAMPLE_CLUSTERS } from '../fixtures/sampleClusters'

export function MapPage() {
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [stats, setStats] = useState<ClustersResponse['stats'] | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null)
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
      if (res.clusters.length > 0) {
        setSelectedClusterId(res.clusters[0].clusterId)
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to load satellite fire detections.')
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
          if (res.clusters.length > 0) {
            setSelectedClusterId(res.clusters[0].clusterId)
          }
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
            setError('Failed to load satellite fire detections.')
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
    setSelectedClusterId(SAMPLE_CLUSTERS[0]?.clusterId || null)
    setStats({
      totalClusters: SAMPLE_CLUSTERS.length,
      totalFires: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.count, 0),
      totalFrp: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.totalFrp, 0),
      maxFrp: Math.max(...SAMPLE_CLUSTERS.map((c) => c.maxFrp)),
      avgWindSpeedKmh: 12.0,
    })
    setLastUpdated('2026-10-11T10:30:00Z (Sample Test Data)')
    setIsUsingSampleData(true)
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Top Stats Bar */}
      <div className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center flex-wrap gap-6">
          <div>
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Active Monitoring Day
            </span>
            <span className="font-mono text-data text-text font-medium">
              Today (IST)
            </span>
          </div>
          <div className="border-l border-divider pl-6">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Monitored Corridor
            </span>
            <span className="font-mono text-data text-text">
              Punjab & Haryana
            </span>
          </div>
          {stats && (
            <>
              <div className="border-l border-divider pl-6">
                <span className="font-mono text-[11px] text-text-muted uppercase block">
                  Active Clusters
                </span>
                <span className="font-mono text-data text-text font-semibold">
                  {stats.totalClusters} ({stats.totalFires} detections)
                </span>
              </div>
              <div className="border-l border-divider pl-6 hidden sm:block">
                <span className="font-mono text-[11px] text-text-muted uppercase block">
                  Total Radiative Power
                </span>
                <span className="font-mono text-data text-accent font-semibold">
                  {stats.totalFrp.toFixed(1)} MW
                </span>
              </div>
            </>
          )}
        </div>

        <div className="font-mono text-small text-text-muted">
          Last Updated:{' '}
          <span className="text-text">
            {lastUpdated || 'Live Sync'}
          </span>
          {isUsingSampleData && (
            <span className="ml-2 px-1.5 py-0.5 bg-surface border border-neutral-low text-neutral-low text-[10px]">
              Fixtures Preview
            </span>
          )}
        </div>
      </div>

      {/* Async State: Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          <LoadingSkeleton height="h-[240px]" lines={4} />
          <LoadingSkeleton height="h-[120px]" lines={3} />
        </div>
      )}

      {/* Async State: Error Message with Retry & Fallback to Sample Telemetry */}
      {!isLoading && error && (
        <div className="space-y-4">
          <ErrorMessage
            title="Failed to Load Fire Telemetry"
            message={`${error}. The surveillance API may be offline or unconfigured in this environment.`}
            onRetry={fetchClusters}
          />
          <div className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-small font-medium text-text block">
                Local Development / Inspection Mode
              </span>
              <span className="text-[12px] text-text-muted">
                Load sample cluster telemetry fixtures to inspect the Leaflet map and companion table.
              </span>
            </div>
            <button
              type="button"
              onClick={loadSampleData}
              className="bg-accent hover:bg-accent-hover text-white text-small px-4 py-2 border-0 font-medium transition-colors cursor-pointer"
            >
              Load Sample Telemetry Fixtures
            </button>
          </div>
        </div>
      )}

      {/* Async State: Empty State */}
      {!isLoading && !error && clusters.length === 0 && (
        <div className="space-y-4">
          <EmptyState
            title="No Fire Detections Today"
            message="No satellite fire clusters have been detected in Punjab and Haryana for the active monitoring window."
          />
          <div className="border border-divider bg-surface p-4 flex items-center justify-between">
            <span className="text-small text-text-muted">
              Inspect map controls and divIcon styling using sample telemetry:
            </span>
            <button
              type="button"
              onClick={loadSampleData}
              className="bg-accent hover:bg-accent-hover text-white text-small px-4 py-2 border-0 font-medium transition-colors cursor-pointer"
            >
              Load Sample Telemetry Fixtures
            </button>
          </div>
        </div>
      )}

      {/* Active Data: Map and Companion Table */}
      {!isLoading && !error && clusters.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Left Column: Interactive Map & Companion Table (2/3 width) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="border border-divider bg-surface p-4 flex flex-col">
              <div className="flex justify-between items-center border-b border-divider pb-3 mb-4">
                <div>
                  <h1 className="text-h3 font-semibold text-text m-0">
                    Surveillance Map
                  </h1>
                  <span className="font-mono text-[12px] text-text-muted">
                    Thermal fire clusters scaled by FRP with directional wind vectors
                  </span>
                </div>
                <span className="font-mono text-[12px] bg-bg border border-divider px-2 py-1 text-text-muted">
                  WGS 84
                </span>
              </div>

              {/* React-Leaflet Map Component */}
              <ClusterMap
                clusters={clusters}
                selectedClusterId={selectedClusterId}
                onSelectCluster={setSelectedClusterId}
                height="500px"
              />

              {/* Legend & Attribution Bar */}
              <div className="flex flex-wrap items-center justify-between text-[12px] text-text-muted mt-3 pt-3 border-t border-divider gap-3">
                <div className="flex items-center flex-wrap gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-accent inline-block border border-[#78270E]" />
                    <span className="font-medium text-text">High Severity</span> (&ge;500 MW)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-accent-mid inline-block border border-[#7B3116]" />
                    <span className="font-medium text-text">Medium Severity</span> (&ge;150 MW)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 border-2 border-neutral-low bg-bg inline-block" />
                    <span className="font-medium text-text">Low Severity</span> (&lt;150 MW)
                  </span>
                </div>
                <span className="font-mono text-[11px]">
                  OpenStreetMap Attribution Active
                </span>
              </div>
            </div>

            {/* Keyboard-Accessible Companion Table */}
            <ClusterCompanionTable
              clusters={clusters}
              selectedClusterId={selectedClusterId}
              onSelectCluster={setSelectedClusterId}
            />
          </div>

          {/* Right Column: Cities at Risk & Alert Subscription Panel (1/3 width) */}
          <div className="border border-divider bg-surface p-5 space-y-6">
            <div>
              <h2 className="text-h3 font-semibold text-text mb-1">
                Monitored Corridor
              </h2>
              <p className="text-small text-text-muted m-0">
                Downwind smoke arrival estimates based on prevailing wind vectors.
              </p>
            </div>

            <div className="border border-divider bg-bg p-4 space-y-3">
              <span className="font-mono text-[12px] text-text-muted uppercase block">
                Selected Cluster
              </span>
              {selectedClusterId ? (
                <div className="space-y-2 text-small">
                  <div className="flex justify-between border-b border-divider pb-1">
                    <span className="text-text-muted">Identifier:</span>
                    <span className="font-mono font-semibold text-text">
                      {selectedClusterId}
                    </span>
                  </div>
                  {clusters.find((c) => c.clusterId === selectedClusterId) && (
                    <>
                      <div className="flex justify-between border-b border-divider pb-1">
                        <span className="text-text-muted">Centroid:</span>
                        <span className="font-mono text-text">
                          {clusters.find((c) => c.clusterId === selectedClusterId)?.lat.toFixed(3)},{' '}
                          {clusters.find((c) => c.clusterId === selectedClusterId)?.lon.toFixed(3)}
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-divider pb-1">
                        <span className="text-text-muted">Total Power:</span>
                        <span className="font-mono font-semibold text-accent">
                          {clusters.find((c) => c.clusterId === selectedClusterId)?.totalFrp.toFixed(1)} MW
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">Wind Vector:</span>
                        <span className="font-mono text-text">
                          {clusters.find((c) => c.clusterId === selectedClusterId)?.windSpeedKmh.toFixed(1)} km/h @{' '}
                          {Math.round(clusters.find((c) => c.clusterId === selectedClusterId)?.windDirDeg || 0)}°
                        </span>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-small text-text-muted m-0">
                  Select a marker on the map or a row in the table to view detailed trajectory data.
                </p>
              )}
            </div>

            {/* Subscribe Box */}
            <div className="border border-divider bg-bg p-4 space-y-3">
              <span className="font-mono text-[12px] text-text-muted uppercase block">
                Email Smoke Alerts
              </span>
              <p className="text-small text-text-muted m-0">
                Receive automated notifications when high severity smoke trajectories target monitored cities (12h cooldown guard).
              </p>
              <div className="text-[12px] text-text-muted font-mono">
                Double opt-in verified • Zero spam
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
