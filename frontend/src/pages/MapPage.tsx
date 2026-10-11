import { useState, useEffect, useCallback } from 'react'
import { apiClient, ApiClientError } from '../api/client'
import type { Cluster, ClustersResponse, Impact, ImpactResponse, City } from '../types/api'
import { ClusterMap, ClusterCompanionTable } from '../components/ClusterMap'
import { CitiesAtRiskPanel } from '../components/CitiesAtRiskPanel'
import { SubscribeForm } from '../components/SubscribeForm'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { ErrorMessage } from '../components/ErrorMessage'
import { EmptyState } from '../components/EmptyState'
import { fetchCitiesAirQuality, type CityAirQuality } from '../api/airQuality'
import { SAMPLE_CLUSTERS } from '../fixtures/sampleClusters'
import { SAMPLE_IMPACTS } from '../fixtures/sampleImpact'

export function MapPage() {
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [impacts, setImpacts] = useState<Impact[]>([])
  const [citiesList, setCitiesList] = useState<City[]>([])
  const [clusterStats, setClusterStats] = useState<ClustersResponse['stats'] | null>(null)
  const [impactStats, setImpactStats] = useState<ImpactResponse['stats'] | null>(null)
  const [airQualityMap, setAirQualityMap] = useState<Record<string, CityAirQuality>>({})
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null)
  const [selectedCityId, setSelectedCityId] = useState<string | null>(null)
  const [activeDate, setActiveDate] = useState<string>('') // Empty string = today (NRT)
  const [isLoading, setIsLoading] = useState(true)
  const [isAqLoading, setIsAqLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isUsingSampleData, setIsUsingSampleData] = useState(false)

  useEffect(() => {
    let isCancelled = false
    const queryParam = activeDate ? { day: activeDate } : undefined

    Promise.all([
      apiClient.getClusters(queryParam),
      apiClient.getImpact(queryParam),
      apiClient.getCities().catch(() => ({ cities: [] as City[], total: 0 })),
    ])
      .then(([clustersRes, impactRes, citiesRes]) => {
        if (!isCancelled) {
          setClusters(clustersRes.clusters)
          setClusterStats(clustersRes.stats)
          setImpacts(impactRes.impact)
          setImpactStats(impactRes.stats)
          setCitiesList(citiesRes.cities)
          setLastUpdated(clustersRes.lastUpdatedUtc || impactRes.lastUpdatedUtc || null)
          setIsUsingSampleData(false)
          setSelectedClusterId(clustersRes.clusters[0]?.clusterId || null)
          setSelectedCityId(impactRes.impact[0]?.cityId || null)
          setError(null)
          setIsLoading(false)

          if (citiesRes.cities.length > 0) {
            setIsAqLoading(true)
            fetchCitiesAirQuality(citiesRes.cities)
              .then((aqMap) => {
                if (!isCancelled) setAirQualityMap(aqMap)
              })
              .catch(() => {})
              .finally(() => {
                if (!isCancelled) setIsAqLoading(false)
              })
          }
        }
      })
      .catch((err: unknown) => {
        if (!isCancelled) {
          if (err instanceof ApiClientError) {
            setError(err.message)
          } else if (err instanceof Error) {
            setError(err.message)
          } else {
            setError('Failed to load surveillance telemetry.')
          }
          setIsLoading(false)
        }
      })

    return () => {
      isCancelled = true
    }
  }, [activeDate])

  const handleRetry = useCallback(() => {
    setIsLoading(true)
    setError(null)
    const queryParam = activeDate ? { day: activeDate } : undefined
    Promise.all([
      apiClient.getClusters(queryParam),
      apiClient.getImpact(queryParam),
      apiClient.getCities().catch(() => ({ cities: [] as City[], total: 0 })),
    ])
      .then(([clustersRes, impactRes, citiesRes]) => {
        setClusters(clustersRes.clusters)
        setClusterStats(clustersRes.stats)
        setImpacts(impactRes.impact)
        setImpactStats(impactRes.stats)
        setCitiesList(citiesRes.cities)
        setLastUpdated(clustersRes.lastUpdatedUtc || impactRes.lastUpdatedUtc || null)
        setIsUsingSampleData(false)
        setSelectedClusterId(clustersRes.clusters[0]?.clusterId || null)
        setSelectedCityId(impactRes.impact[0]?.cityId || null)
        setError(null)
        setIsLoading(false)

        if (citiesRes.cities.length > 0) {
          setIsAqLoading(true)
          fetchCitiesAirQuality(citiesRes.cities)
            .then((aqMap) => setAirQualityMap(aqMap))
            .catch(() => {})
            .finally(() => setIsAqLoading(false))
        }
      })
      .catch((err: unknown) => {
        if (err instanceof ApiClientError) {
          setError(err.message)
        } else if (err instanceof Error) {
          setError(err.message)
        } else {
          setError('Failed to load surveillance telemetry.')
        }
        setIsLoading(false)
      })
  }, [activeDate])


  const loadSampleData = () => {
    setClusters(SAMPLE_CLUSTERS)
    setImpacts(SAMPLE_IMPACTS)
    setSelectedClusterId(SAMPLE_CLUSTERS[0]?.clusterId || null)
    setSelectedCityId(SAMPLE_IMPACTS[0]?.cityId || null)
    setClusterStats({
      totalClusters: SAMPLE_CLUSTERS.length,
      totalFires: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.count, 0),
      totalFrp: SAMPLE_CLUSTERS.reduce((acc, c) => acc + c.totalFrp, 0),
      maxFrp: Math.max(...SAMPLE_CLUSTERS.map((c) => c.maxFrp)),
      avgWindSpeedKmh: 12.0,
    })
    setImpactStats({
      totalCitiesAffected: SAMPLE_IMPACTS.length,
      highSeverityCount: SAMPLE_IMPACTS.filter((i) => i.severity === 'High').length,
      mediumSeverityCount: SAMPLE_IMPACTS.filter((i) => i.severity === 'Medium').length,
      lowSeverityCount: SAMPLE_IMPACTS.filter((i) => i.severity === 'Low').length,
      maxCityFrp: Math.max(...SAMPLE_IMPACTS.map((i) => i.totalFrp)),
    })
    setAirQualityMap({
      delhi: { cityId: 'delhi', usAqi: 159, pm25: 69.2 },
      chandigarh: { cityId: 'chandigarh', usAqi: 103, pm25: 65.4 },
      karnal: { cityId: 'karnal', usAqi: 142, pm25: 58.1 },
      patiala: { cityId: 'patiala', usAqi: 128, pm25: 52.0 },
      ambala: { cityId: 'ambala', usAqi: 115, pm25: 48.3 },
      jalandhar: { cityId: 'jalandhar', usAqi: 135, pm25: 55.0 },
      panipat: { cityId: 'panipat', usAqi: 148, pm25: 62.4 },
      hisar: { cityId: 'hisar', usAqi: 120, pm25: 49.0 },
    })
    setLastUpdated('Today (Sample Telemetry Fixtures)')
    setIsUsingSampleData(true)
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Top Computed Stats Bar */}
      <section
        className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4"
        aria-label="Active Surveillance Summary Statistics"
      >
        <div className="flex items-center flex-wrap gap-4 sm:gap-6">
          {/* Active Date / Window */}
          <div>
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Monitoring Window
            </span>
            <span className="font-mono text-data text-text font-medium">
              {activeDate ? `${activeDate} (Archive)` : 'Today (IST NRT)'}
            </span>
          </div>

          {/* Active Clusters & Detections */}
          <div className="border-l border-divider pl-4 sm:pl-6">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Active Clusters
            </span>
            <span className="font-mono text-data text-text font-semibold">
              {clusterStats ? (
                `${clusterStats.totalClusters} (${clusterStats.totalFires} fires)`
              ) : (
                '0'
              )}
            </span>
          </div>

          {/* Total Radiative Power */}
          <div className="border-l border-divider pl-4 sm:pl-6">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Total Fire Power
            </span>
            <span className="font-mono text-data text-accent font-semibold">
              {clusterStats ? `${clusterStats.totalFrp.toFixed(1)} MW` : '0.0 MW'}
            </span>
          </div>

          {/* Avg Wind Speed */}
          <div className="border-l border-divider pl-4 sm:pl-6 hidden md:block">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Average Wind
            </span>
            <span className="font-mono text-data text-text">
              {clusterStats ? `${clusterStats.avgWindSpeedKmh.toFixed(1)} km/h` : '0.0 km/h'}
            </span>
          </div>

          {/* Cities at Risk Count */}
          <div className="border-l border-divider pl-4 sm:pl-6">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Cities at Risk
            </span>
            <span className="font-mono text-data text-text font-semibold">
              {impactStats ? (
                `${impactStats.totalCitiesAffected} (${impactStats.highSeverityCount} High, ${impactStats.mediumSeverityCount} Med)`
              ) : (
                '0'
              )}
            </span>
          </div>
        </div>

        {/* Date Selector & Sync Status */}
        <div className="flex items-center gap-3 font-mono text-[12px]">
          {/* Quick Date Switch: Today vs Peak Season Archive 2024-11-01 */}
          <div className="flex items-center border border-divider bg-bg" role="group" aria-label="Surveillance date selection">
            <button
              type="button"
              onClick={() => setActiveDate('')}
              className={`px-2.5 py-1 text-[11px] border-r border-divider transition-colors cursor-pointer ${
                activeDate === ''
                  ? 'bg-text text-white font-medium'
                  : 'bg-transparent text-text hover:bg-hover'
              }`}
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => setActiveDate('2024-11-01')}
              className={`px-2.5 py-1 text-[11px] transition-colors cursor-pointer ${
                activeDate === '2024-11-01'
                  ? 'bg-text text-white font-medium'
                  : 'bg-transparent text-text hover:bg-hover'
              }`}
            >
              Peak Season (2024-11-01)
            </button>
          </div>

          <div className="text-text-muted hidden xl:block">
            Sync:{' '}
            <span className="text-text">
              {lastUpdated ? lastUpdated.replace('T', ' ').replace('Z', ' UTC') : 'Real-time'}
            </span>
            {isUsingSampleData && (
              <span className="ml-2 px-1.5 py-0.5 bg-surface border border-neutral-low text-neutral-low text-[10px]">
                Fixtures
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Async State: Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          <LoadingSkeleton height="h-[280px]" lines={4} />
          <LoadingSkeleton height="h-[140px]" lines={3} />
        </div>
      )}

      {/* Async State: Error Message with Retry */}
      {!isLoading && error && (
        <div className="space-y-4">
          <ErrorMessage
            title="Failed to Load Fire Telemetry"
            message={`${error}. Check network connectivity or API deployment.`}
            onRetry={handleRetry}
          />
          <div className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-small font-medium text-text block">
                Offline Inspection Mode
              </span>
              <span className="text-[12px] text-text-muted">
                Load recorded sample telemetry fixtures to inspect the map, smoke direction vectors, and cities-at-risk panel.
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

      {/* Empty State when zero fires in current window */}
      {!isLoading && !error && clusters.length === 0 && (
        <div className="space-y-4">
          <EmptyState
            title="No Fire Detections for Selected Window"
            message="No satellite fire clusters have been recorded in Punjab and Haryana for this observation window. During the off-season, active burns are zero or near zero."
          />
          <div className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-small font-medium text-text block">
                Inspect Real Historical Stubble Burning Telemetry
              </span>
              <span className="text-[12px] text-text-muted">
                View 428 real clusters and 15 affected cities from the deployed DynamoDB archive (November 1, 2024 peak stubble season):
              </span>
            </div>
            <button
              type="button"
              onClick={() => setActiveDate('2024-11-01')}
              className="bg-accent hover:bg-accent-hover text-white text-small px-4 py-2 border-0 font-medium transition-colors cursor-pointer"
            >
              View 2024-11-01 Peak Season Telemetry
            </button>
          </div>
        </div>
      )}

      {/* Active Data Layout: Map (Left) & Cities-At-Risk Panel (Right), Stacked on Mobile */}
      {!isLoading && !error && clusters.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Left Column: Interactive Map & Companion Table (2/3 width on desktop) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="border border-divider bg-surface p-4 flex flex-col">
              <div className="flex justify-between items-center border-b border-divider pb-3 mb-4">
                <div>
                  <h1 className="text-h3 font-semibold text-text m-0">
                    Surveillance Map
                  </h1>
                  <span className="font-mono text-[12px] text-text-muted">
                    Thermal fire clusters scaled by FRP with estimated smoke direction vectors
                  </span>
                </div>
                <span className="font-mono text-[12px] bg-bg border border-divider px-2 py-1 text-text-muted">
                  WGS 84
                </span>
              </div>

              {/* React-Leaflet Map Component with square divIcons and directional smoke vectors */}
              <ClusterMap
                clusters={clusters}
                selectedClusterId={selectedClusterId}
                onSelectCluster={setSelectedClusterId}
                height="500px"
              />

              {/* Legend & Attribution Bar with explicit 'Estimated smoke direction' entry */}
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
                  <span className="flex items-center gap-1.5 border-l border-divider pl-3">
                    <span className="w-4 h-[2px] bg-accent inline-block border-t border-b border-[#78270E]" />
                    <span className="font-medium text-text">Estimated smoke direction</span>
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

          {/* Right Column: Cities-at-Risk Panel & Selected Cluster Inspection (1/3 width on desktop, stacked on mobile) */}
          <div className="space-y-6">
            {/* Cities-at-Risk Panel with city, ETA, text severity, baseline AQI modelled estimate */}
            <CitiesAtRiskPanel
              impacts={impacts}
              airQualityMap={airQualityMap}
              selectedCityId={selectedCityId}
              onSelectCity={setSelectedCityId}
              isLoading={isAqLoading}
            />

            {/* Accessible Subscribe Form (T-058) */}
            <SubscribeForm
              cities={citiesList}
              defaultCityId={selectedCityId || undefined}
            />

            {/* Selected Cluster Details Card */}
            <div className="border border-divider bg-surface p-5 space-y-3">
              <span className="font-mono text-[12px] text-text-muted uppercase block">
                Selected Cluster Details
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
                      <div className="flex justify-between border-b border-divider pb-1">
                        <span className="text-text-muted">Wind Speed:</span>
                        <span className="font-mono text-text">
                          {clusters.find((c) => c.clusterId === selectedClusterId)?.windSpeedKmh.toFixed(1)} km/h @{' '}
                          {Math.round(clusters.find((c) => c.clusterId === selectedClusterId)?.windDirDeg || 0)}°
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">Estimated Smoke:</span>
                        <span className="font-mono text-accent font-semibold">
                          {Math.round(
                            ((clusters.find((c) => c.clusterId === selectedClusterId)?.windDirDeg || 0) + 180) % 360
                          )}° (Downwind)
                        </span>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-small text-text-muted m-0">
                  Select a marker on the map or a row in the table to inspect detailed coordinates and wind vector.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
