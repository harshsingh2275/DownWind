import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import type { Cluster } from '../types/api'
import {
  DEFAULT_TILE_URL,
  DEFAULT_TILE_ATTRIBUTION,
  DEFAULT_MAP_CENTER,
  DEFAULT_MAP_ZOOM,
} from '../config'
import {
  getClusterSeverity,
  createClusterDivIcon,
} from './clusterMapUtils'

/**
 * Pan controller component to pan map when a cluster is selected.
 */
function MapViewController({
  selectedCluster,
}: {
  selectedCluster: Cluster | null | undefined
}) {
  const map = useMap()

  useEffect(() => {
    if (selectedCluster) {
      map.panTo([selectedCluster.lat, selectedCluster.lon], {
        animate: true,
        duration: 0.6,
      })
    }
  }, [map, selectedCluster])

  return null
}

export interface ClusterMapProps {
  clusters: Cluster[]
  selectedClusterId?: string | null
  onSelectCluster?: (clusterId: string) => void
  className?: string
  height?: string
}

/**
 * Interactive React-Leaflet Map component (T-054).
 * Conforms to design.md §7:
 * - Square divIcon markers sized by FRP (clamped 12px-32px)
 * - Severity encoded by fill & border
 * - 0px border radius, no shadow on popups, controls, and attribution
 * - OpenStreetMap attribution strictly visible
 */
export function ClusterMap({
  clusters,
  selectedClusterId,
  onSelectCluster,
  className = '',
  height = '480px',
}: ClusterMapProps) {
  const selectedCluster = useMemo(
    () => clusters.find((c) => c.clusterId === selectedClusterId) || null,
    [clusters, selectedClusterId],
  )

  return (
    <div
      className={`border border-divider bg-surface relative overflow-hidden ${className}`}
      style={{ height }}
      data-testid="cluster-map-container"
    >
      <MapContainer
        center={DEFAULT_MAP_CENTER}
        zoom={DEFAULT_MAP_ZOOM}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%' }}
        className="w-full h-full"
      >
        <MapViewController selectedCluster={selectedCluster} />

        <TileLayer
          attribution={DEFAULT_TILE_ATTRIBUTION}
          url={DEFAULT_TILE_URL}
          maxZoom={18}
          minZoom={5}
        />

        {clusters.map((cluster) => {
          const isSelected = cluster.clusterId === selectedClusterId
          const icon = createClusterDivIcon(cluster, isSelected)
          const severity = getClusterSeverity(cluster)

          return (
            <Marker
              key={cluster.clusterId}
              position={[cluster.lat, cluster.lon]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectCluster?.(cluster.clusterId),
              }}
            >
              <Popup>
                <div className="space-y-2 py-1">
                  <div className="flex items-center justify-between gap-3 border-b border-divider pb-1.5">
                    <span className="font-mono text-[12px] font-semibold text-text uppercase">
                      {cluster.clusterId}
                    </span>
                    <span
                      className={`font-mono text-[11px] px-1.5 py-0.5 border ${
                        severity === 'High'
                          ? 'bg-accent text-white border-accent'
                          : severity === 'Medium'
                            ? 'bg-accent-mid text-white border-accent-mid'
                            : 'bg-transparent text-neutral-low border-neutral-low'
                      }`}
                    >
                      {severity} Severity
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[12px]">
                    <div>
                      <span className="text-text-muted block text-[11px]">Centroid</span>
                      <span className="font-mono text-data text-text">
                        {cluster.lat.toFixed(3)}, {cluster.lon.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[11px]">Total FRP</span>
                      <span className="font-mono text-data text-text font-semibold">
                        {cluster.totalFrp.toFixed(1)} MW
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[11px]">Fires Count</span>
                      <span className="font-mono text-data text-text">
                        {cluster.count} detections
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[11px]">Peak Single FRP</span>
                      <span className="font-mono text-data text-text">
                        {cluster.maxFrp.toFixed(1)} MW
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-divider pt-1.5 text-[11px] text-text-muted flex justify-between items-center">
                    <span>
                      Wind: <strong className="font-mono text-text">{cluster.windSpeedKmh.toFixed(1)} km/h</strong> @ {Math.round(cluster.windDirDeg)}°
                    </span>
                    <span className="font-mono text-[10px]">
                      Estimate
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}

export interface ClusterCompanionTableProps {
  clusters: Cluster[]
  selectedClusterId?: string | null
  onSelectCluster?: (clusterId: string) => void
  className?: string
}

/**
 * Keyboard-accessible Cluster Table Companion (design.md §7 & T-054).
 * Provides an accessible tabular alternative for screen readers and keyboard navigation.
 */
export function ClusterCompanionTable({
  clusters,
  selectedClusterId,
  onSelectCluster,
  className = '',
}: ClusterCompanionTableProps) {
  return (
    <div
      className={`border border-divider bg-surface p-4 flex flex-col ${className}`}
      role="region"
      aria-label="Clusters accessible telemetry table"
    >
      <div className="flex justify-between items-baseline mb-3 border-b border-divider pb-2">
        <h2 className="text-h3 font-semibold text-text m-0">
          Detected Fire Clusters
        </h2>
        <span className="font-mono text-small text-text-muted">
          {clusters.length} {clusters.length === 1 ? 'Cluster' : 'Clusters'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table
          className="w-full text-left border-collapse text-small"
          aria-label="Fire clusters with location, FRP intensity, and severity"
        >
          <caption className="sr-only">
            Active fire clusters in Punjab and Haryana with coordinates, FRP intensity, fire counts, and calculated severity.
          </caption>
          <thead>
            <tr className="border-b border-divider bg-surface text-text-muted text-[12px] font-mono">
              <th scope="col" className="py-2 px-3 font-medium">Cluster ID</th>
              <th scope="col" className="py-2 px-3 font-medium">Centroid (Lat, Lon)</th>
              <th scope="col" className="py-2 px-3 font-medium text-right">FRP (MW)</th>
              <th scope="col" className="py-2 px-3 font-medium text-right">Detections</th>
              <th scope="col" className="py-2 px-3 font-medium">Severity</th>
              <th scope="col" className="py-2 px-3 font-medium text-right">Wind</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-divider bg-bg">
            {clusters.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-text-muted text-small">
                  No fire clusters available for the selected period.
                </td>
              </tr>
            ) : (
              clusters.map((cluster) => {
                const isSelected = cluster.clusterId === selectedClusterId
                const severity = getClusterSeverity(cluster)

                return (
                  <tr
                    key={cluster.clusterId}
                    tabIndex={0}
                    role="button"
                    aria-label={`Select cluster ${cluster.clusterId}, ${cluster.totalFrp} MW, ${severity} severity`}
                    aria-selected={isSelected}
                    onClick={() => onSelectCluster?.(cluster.clusterId)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onSelectCluster?.(cluster.clusterId)
                      }
                    }}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-hover border-l-2 border-l-focus'
                        : 'hover:bg-hover'
                    }`}
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-text">
                      {cluster.clusterId}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-data text-text">
                      {cluster.lat.toFixed(3)}, {cluster.lon.toFixed(3)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-data text-right font-semibold text-text">
                      {cluster.totalFrp.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-data text-right text-text">
                      {cluster.count}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="flex items-center gap-2">
                        <span
                          className={`w-2.5 h-2.5 inline-block ${
                            severity === 'High'
                              ? 'bg-accent'
                              : severity === 'Medium'
                                ? 'bg-accent-mid'
                                : 'border border-neutral-low bg-bg'
                          }`}
                          aria-hidden="true"
                        />
                        <span className="font-medium text-text">
                          {severity}
                        </span>
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-data text-right text-text-muted">
                      {cluster.windSpeedKmh.toFixed(0)} km/h @ {Math.round(cluster.windDirDeg)}°
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 pt-2 border-t border-divider flex items-center justify-between text-[11px] text-text-muted">
        <span>Use <kbd className="font-mono px-1 border border-divider bg-surface">Tab</kbd> + <kbd className="font-mono px-1 border border-divider bg-surface">Enter</kbd> to inspect a cluster on the map.</span>
        <span className="font-mono">FRP: MW • Indicative</span>
      </div>
    </div>
  )
}
