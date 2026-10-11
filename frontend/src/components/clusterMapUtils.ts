import L from 'leaflet'
import type { Cluster, Severity } from '../types/api'

/**
 * FRP-based sizing formula (clamped between 12px and 32px) per design.md §7.
 */
export function getClusterMarkerSize(totalFrp: number): number {
  if (totalFrp <= 0) return 12
  const scaled = Math.round(10 + Math.sqrt(totalFrp) * 0.7)
  return Math.min(32, Math.max(12, scaled))
}

/**
 * Severity determination per design.md §4 & D-021:
 * High: FRP >= 500 MW
 * Medium: FRP >= 150 MW
 * Low: otherwise
 */
export function getClusterSeverity(cluster: Cluster): Severity {
  if (cluster.totalFrp >= 500) return 'High'
  if (cluster.totalFrp >= 150) return 'Medium'
  return 'Low'
}

/**
 * Creates Leaflet divIcon square marker (0px radius) per design.md §7.
 */
export function createClusterDivIcon(cluster: Cluster, isSelected = false): L.DivIcon {
  const size = getClusterMarkerSize(cluster.totalFrp)
  const severity = getClusterSeverity(cluster)

  let severityModifier = 'marker-severity-low'
  if (severity === 'High') {
    severityModifier = 'marker-severity-high'
  } else if (severity === 'Medium') {
    severityModifier = 'marker-severity-mid'
  }

  const selectedModifier = isSelected ? 'marker-selected' : ''

  return L.divIcon({
    className: 'downwind-div-icon',
    html: `<div class="downwind-square-marker ${severityModifier} ${selectedModifier}" style="width:${size}px;height:${size}px;" role="img" aria-label="Fire cluster ${cluster.clusterId}, ${cluster.totalFrp} MW, ${severity} severity"></div>`,
    iconSize: [size, size],
    iconAnchor: [Math.floor(size / 2), Math.floor(size / 2)],
    popupAnchor: [0, -Math.floor(size / 2)],
  })
}
