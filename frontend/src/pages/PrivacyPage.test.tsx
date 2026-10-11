// @vitest-environment happy-dom
import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import { PrivacyPage } from './PrivacyPage'

describe('PrivacyPage Component (T-062)', () => {
  it('renders visible Draft, pending review notice', () => {
    const rawHtml = renderToString(<PrivacyPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Draft, pending review')
    expect(html).toContain('Action M-12')
  })

  it('accurately documents zero tracking and self-hosted fonts', () => {
    const rawHtml = renderToString(<PrivacyPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Zero Visitor Tracking and Zero Third-Party Analytics')
    expect(html).toContain('No tracking cookies')
    expect(html).toContain('Self-Hosted Typography Assets')
    expect(html).toContain('Public Sans, IBM Plex Mono, and Noto Sans Devanagari')
  })

  it('documents factual AWS SNS subscription and logging architecture', () => {
    const rawHtml = renderToString(<PrivacyPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Email Alert Subscriptions and AWS SNS')
    expect(html).toContain('No Application Subscriber Database')
    expect(html).toContain('Mandatory Double Opt-In Verification')
    expect(html).toContain('Unsubscribe at Any Time')
    expect(html).toContain('PII Masking')
    expect(html).toContain('Server Logs and Data Retention')
  })

  it('clearly marks all missing business details for operator confirmation', () => {
    const rawHtml = renderToString(<PrivacyPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('[OPERATOR_NAME: Pending review (M-12)]')
    expect(html).toContain('[CONTACT_EMAIL: Pending review (M-12)]')
    expect(html).toContain('[LEGAL_JURISDICTION: Pending review (M-12)]')
    expect(html).toContain('[DATA_RETENTION_PERIOD: Default 30 days, pending review (M-12)]')
  })

  it('strictly contains zero em dashes and zero en dashes in copy', () => {
    const rawHtml = renderToString(<PrivacyPage />)
    expect(rawHtml).not.toContain('—')
    expect(rawHtml).not.toContain('–')
  })
})
