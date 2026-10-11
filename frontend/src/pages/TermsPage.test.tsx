// @vitest-environment happy-dom
import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import { TermsPage } from './TermsPage'

describe('TermsPage Component (T-062)', () => {
  it('renders visible Draft, pending review notice', () => {
    const rawHtml = renderToString(<TermsPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Draft, pending review')
    expect(html).toContain('Action M-12')
  })

  it('renders Terms of Use heading and core sections', () => {
    const rawHtml = renderToString(<TermsPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('Terms of Use')
    expect(html).toContain('Public Interest and Educational Purpose')
    expect(html).toContain('No Guarantee of Atmospheric Accuracy')
    expect(html).toContain('Acceptable Use and Subscription Abuse')
    expect(html).toContain('Limitation of Liability')
  })

  it('clearly marks missing business details for operator confirmation', () => {
    const rawHtml = renderToString(<TermsPage />)
    const html = rawHtml.replace(/<!--.*?-->/g, '')

    expect(html).toContain('[OPERATOR_NAME: Pending review (M-12)]')
    expect(html).toContain('[LEGAL_JURISDICTION: Pending review (M-12)]')
    expect(html).toContain('[CONTACT_EMAIL: Pending review (M-12)]')
  })

  it('strictly contains zero em dashes and zero en dashes in copy', () => {
    const rawHtml = renderToString(<TermsPage />)
    expect(rawHtml).not.toContain('—')
    expect(rawHtml).not.toContain('–')
  })
})
