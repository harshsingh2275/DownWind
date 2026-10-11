// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderToString } from 'react-dom/server'
import { SubscribeForm } from './SubscribeForm'
import type { City } from '../types/api'

const TEST_CITIES: City[] = [
  { id: 'chandigarh', name: 'Chandigarh', state: 'Chandigarh', lat: 30.73, lon: 76.78, population: 1055450 },
  { id: 'delhi', name: 'Delhi', state: 'Delhi', lat: 28.61, lon: 77.23, population: 16787941 },
  { id: 'karnal', name: 'Karnal', state: 'Haryana', lat: 29.69, lon: 76.99, population: 286974 },
]

describe('SubscribeForm Component (T-058)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders visible form labels for city and email fields', () => {
    const rawHtml = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="chandigarh" />
    )
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    // Visible labels
    expect(html).toContain('Select Monitored City')
    expect(html).toContain('Email Address')
    expect(html).toContain('<label')
  })

  it('renders dynamic button label: Subscribe to alerts for <city>', () => {
    const htmlChandigarh = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="chandigarh" />
    ).replace(/<!--.*?-->/g, '')
    expect(htmlChandigarh).toContain('Subscribe to alerts for Chandigarh')

    const htmlDelhi = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="delhi" />
    ).replace(/<!--.*?-->/g, '')
    expect(htmlDelhi).toContain('Subscribe to alerts for Delhi')
  })

  it('links inputs with help and description attributes (aria-describedby)', () => {
    const rawHtml = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="chandigarh" />
    )
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('aria-describedby')
    expect(html).toContain('type="email"')
    expect(html).toContain('min-h-[44px]')
  })

  it('renders privacy link near the form', () => {
    const rawHtml = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="chandigarh" />
    )
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Privacy Policy')
    expect(html).toContain('href="/privacy"')
    expect(html).toContain('12h cooldown')
  })

  it('renders semantic form elements and accessible region landmark', () => {
    const rawHtml = renderToString(
      <SubscribeForm cities={TEST_CITIES} defaultCityId="karnal" />
    )
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('role="region"')
    expect(html).toContain('aria-label="Smoke alert email subscription"')
    expect(html).toContain('<form')
    expect(html).toContain('Subscribe to alerts for Karnal')
  })
})
