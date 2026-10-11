// @vitest-environment happy-dom
import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import {
  ClusterCompanionTable,
} from './ClusterMap'
import {
  getClusterMarkerSize,
  getClusterSeverity,
  createClusterDivIcon,
} from './clusterMapUtils'
import { SAMPLE_CLUSTERS } from '../fixtures/sampleClusters'

describe('ClusterMap Utilities', () => {
  describe('getClusterMarkerSize', () => {
    it('clamps to minimum size (12px) for zero or low FRP', () => {
      expect(getClusterMarkerSize(0)).toBe(12)
      expect(getClusterMarkerSize(-10)).toBe(12)
      expect(getClusterMarkerSize(4)).toBe(12)
    })

    it('scales monotonically for moderate FRP values', () => {
      const sizeLow = getClusterMarkerSize(50)
      const sizeMed = getClusterMarkerSize(200)
      const sizeHigh = getClusterMarkerSize(600)

      expect(sizeLow).toBeGreaterThanOrEqual(12)
      expect(sizeMed).toBeGreaterThan(sizeLow)
      expect(sizeHigh).toBeGreaterThan(sizeMed)
      expect(sizeHigh).toBeLessThanOrEqual(32)
    })

    it('clamps to maximum size (32px) for extreme FRP values', () => {
      expect(getClusterMarkerSize(2000)).toBe(32)
      expect(getClusterMarkerSize(10000)).toBe(32)
    })
  })

  describe('getClusterSeverity', () => {
    it('identifies High severity (FRP >= 500)', () => {
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 500 })).toBe('High')
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 1200 })).toBe('High')
    })

    it('identifies Medium severity (150 <= FRP < 500)', () => {
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 150 })).toBe('Medium')
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 499.9 })).toBe('Medium')
    })

    it('identifies Low severity (FRP < 150)', () => {
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 149.9 })).toBe('Low')
      expect(getClusterSeverity({ ...SAMPLE_CLUSTERS[0], totalFrp: 20 })).toBe('Low')
    })
  })

  describe('createClusterDivIcon', () => {
    it('creates square divIcon with severity-high class for high FRP', () => {
      const icon = createClusterDivIcon(SAMPLE_CLUSTERS[0]) // FRP 620.5 -> High
      expect(icon.options.className).toBe('downwind-div-icon')
      expect(icon.options.html).toContain('marker-severity-high')
      expect(icon.options.html).toContain('role="img"')
      expect(icon.options.iconSize).toBeDefined()
      if (Array.isArray(icon.options.iconSize)) {
        // Must be square: width === height
        expect(icon.options.iconSize[0]).toBe(icon.options.iconSize[1])
      }
    })

    it('creates divIcon with severity-low class for low FRP', () => {
      const icon = createClusterDivIcon(SAMPLE_CLUSTERS[2]) // FRP 75.2 -> Low
      expect(icon.options.html).toContain('marker-severity-low')
    })

    it('applies marker-selected class when isSelected is true', () => {
      const icon = createClusterDivIcon(SAMPLE_CLUSTERS[0], true)
      expect(icon.options.html).toContain('marker-selected')
    })
  })
})

describe('ClusterCompanionTable Component', () => {
  it('renders semantic table structure with caption and headers', () => {
    const html = renderToString(
      <ClusterCompanionTable
        clusters={SAMPLE_CLUSTERS}
        selectedClusterId="cl-pb-01"
      />,
    )

    expect(html).toContain('<table')
    expect(html).toContain('Active fire clusters in Punjab and Haryana')
    expect(html).toContain('Detected Fire Clusters')
    expect(html).toContain('Cluster ID')
    expect(html).toContain('Centroid (Lat, Lon)')
    expect(html).toContain('FRP (MW)')
    expect(html).toContain('Severity')
  })

  it('renders cluster data with keyboard accessibility attributes', () => {
    const html = renderToString(
      <ClusterCompanionTable
        clusters={SAMPLE_CLUSTERS}
        selectedClusterId="cl-pb-01"
      />,
    )

    expect(html).toContain('cl-pb-01')
    expect(html).toContain('cl-pb-02')
    expect(html).toContain('cl-hr-01')
    expect(html).toContain('tabindex="0"')
    expect(html).toContain('role="button"')
    expect(html).toContain('aria-selected="true"')

    // Explicit text labels for severity per design.md §4
    expect(html).toContain('High')
    expect(html).toContain('Medium')
    expect(html).toContain('Low')
  })

  it('renders empty state when clusters array is empty', () => {
    const html = renderToString(<ClusterCompanionTable clusters={[]} />)
    expect(html).toContain('No fire clusters available for the selected period.')
  })
})
