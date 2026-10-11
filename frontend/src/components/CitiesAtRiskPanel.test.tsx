// @vitest-environment happy-dom
import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import { CitiesAtRiskPanel } from './CitiesAtRiskPanel'
import type { Impact } from '../types/api'

const TEST_IMPACTS: Impact[] = [
  {
    cityId: 'karnal',
    cityName: 'Karnal',
    nClusters: 41,
    totalFrp: 484.2,
    nearestKm: 47.9,
    minEtaHours: 4.5,
    severity: 'Medium',
    affectedByClusterIds: ['c1'],
  },
  {
    cityId: 'delhi',
    cityName: 'Delhi',
    nClusters: 10,
    totalFrp: 620.0,
    nearestKm: 35.0,
    minEtaHours: 2.2,
    severity: 'High',
    affectedByClusterIds: ['c2'],
  },
  {
    cityId: 'amritsar',
    cityName: 'Amritsar',
    nClusters: 3,
    totalFrp: 45.0,
    nearestKm: 12.0,
    minEtaHours: 0.5,
    severity: 'Low',
    affectedByClusterIds: ['c3'],
  },
]

describe('CitiesAtRiskPanel', () => {
  it('renders cities list with name, ETA, and explicit text severity labels', () => {
    const rawHtml = renderToString(
      <CitiesAtRiskPanel
        impacts={TEST_IMPACTS}
        airQualityMap={{
          karnal: { cityId: 'karnal', usAqi: 142, pm25: 58.1 },
          delhi: { cityId: 'delhi', usAqi: 185, pm25: 85.0 },
        }}
      />
    )
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    // Heading
    expect(html).toContain('Cities at Risk')

    // City Names
    expect(html).toContain('Karnal')
    expect(html).toContain('Delhi')
    expect(html).toContain('Amritsar')

    // Explicit severity text labels
    expect(html).toContain('High Severity')
    expect(html).toContain('Medium Severity')
    expect(html).toContain('Low Severity')

    // ETAs formatted
    expect(html).toContain('4h 30m')
    expect(html).toContain('2h 12m')
    expect(html).toContain('30m')

    // Baseline AQI and exact "modelled estimate" label
    expect(html).toContain('142')
    expect(html).toContain('185')
    expect(html).toContain('modelled estimate')
  })

  it('renders empty state when zero cities at risk', () => {
    const html = renderToString(<CitiesAtRiskPanel impacts={[]} />)
    expect(html).toContain('No cities currently in downwind smoke path.')
  })

  it('renders loading skeleton when isLoading is true', () => {
    const html = renderToString(<CitiesAtRiskPanel impacts={[]} isLoading={true} />)
    expect(html).toContain('aria-busy="true"')
  })

  it('provides accessible role and aria attributes for assistive technologies', () => {
    const html = renderToString(
      <CitiesAtRiskPanel
        impacts={TEST_IMPACTS}
        selectedCityId="karnal"
      />
    )
    expect(html).toContain('role="list"')
    expect(html).toContain('role="listitem"')
    expect(html).toContain('tabindex="0"')
    expect(html).toContain('aria-label="Karnal: Severity Medium')
  })
})
