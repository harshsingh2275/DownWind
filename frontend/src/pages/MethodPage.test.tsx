// @vitest-environment happy-dom
import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import { MethodPage } from './MethodPage'

describe('MethodPage Component (T-061)', () => {
  it('renders methodology and data sources heading and technical documentation eyebrow', () => {
    const rawHtml = renderToString(<MethodPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Methodology and Data Sources')
    expect(html).toContain('Technical Documentation')
  })

  it('lists all four data sources without invented claims', () => {
    const rawHtml = renderToString(<MethodPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('NASA FIRMS')
    expect(html).toContain('VIIRS')
    expect(html).toContain('MODIS')
    expect(html).toContain('Open-Meteo Weather')
    expect(html).toContain('Open-Meteo Air Quality')
    expect(html).toContain('geoBoundaries')
    expect(html).toContain('OpenStreetMap')
  })

  it('documents pipeline update frequency and architecture', () => {
    const rawHtml = renderToString(<MethodPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('every 30 minutes')
    expect(html).toContain('EventBridge')
    expect(html).toContain('DynamoDB')
  })

  it('explains the geometric smoke transport algorithm and heuristics', () => {
    const rawHtml = renderToString(<MethodPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('0.05 degree')
    expect(html).toContain('FRP-weighted centroid')
    expect(html).toContain('25 degrees')
    expect(html).toContain('0.85 attenuation')
    expect(html).toContain('12-hour per-city cooldown')
  })

  it('documents every known limitation from PRD section 11', () => {
    const rawHtml = renderToString(<MethodPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Thermal Anomalies vs Confirmed Crop Burns')
    expect(html).toContain('Satellite Orbit Intervals and Latency')
    expect(html).toContain('Cloud Cover and Smog Obscuration')
    expect(html).toContain('Heuristic Corridor vs Numerical Dispersion Models')
    expect(html).toContain('Modelled Air Quality vs Ground Monitoring Stations')
    expect(html).toContain('Unvalidated Heuristic Thresholds')
    expect(html).toContain('Geographic Boundary Scope')
  })

  it('strictly contains zero em dashes and zero en dashes in copy', () => {
    const rawHtml = renderToString(<MethodPage />)
    expect(rawHtml).not.toContain('—') // em dash
    expect(rawHtml).not.toContain('–') // en dash
    expect(rawHtml).not.toContain('&mdash;')
    expect(rawHtml).not.toContain('&ndash;')
  })
})
