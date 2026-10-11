import { PRODUCT_NAME } from '../config'

export function PrivacyPage() {
  return (
    <article className="max-w-[64ch] space-y-8">
      {/* Draft Notice per design.md §8 */}
      <div className="border border-divider bg-surface p-4 text-small">
        <span className="font-mono text-accent font-semibold block uppercase mb-1">
          Notice: Preliminary Draft
        </span>
        <p className="text-text-muted m-0">
          This document is a preliminary operational draft outlining the zero-tracking, privacy-first architecture of {PRODUCT_NAME}.
        </p>
      </div>

      <header className="border-b border-divider pb-6">
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Privacy Policy
        </h1>
        <span className="font-mono text-small text-text-muted block mt-2">
          Effective: October 2026 • Jurisdiction: India
        </span>
      </header>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Zero Visitor Tracking & Zero Third-Party Analytics
        </h2>
        <p className="text-body text-text-muted">
          {PRODUCT_NAME} does not use tracking cookies, browser fingerprinting, advertising beacons, or third-party behavioral analytics (such as Google Analytics or Meta Pixel). Your visits and page views are not recorded or sold.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. Self-Hosted Assets & Font Privacy
        </h2>
        <p className="text-body text-text-muted">
          All typography assets (Public Sans, IBM Plex Mono, Noto Sans Devanagari) are bundled and served directly from our static origin host. No font requests, IP addresses, or client headers are ever shared with third-party content delivery networks (such as Google Fonts).
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. Email Alert Subscriptions
        </h2>
        <p className="text-body text-text-muted">
          When you subscribe to receive smoke advisories for a specific city, your email address is transmitted directly to Amazon Web Services Simple Notification Service (AWS SNS) solely to facilitate automated alert delivery.
        </p>
        <ul className="list-disc pl-5 space-y-2 text-body text-text-muted">
          <li><strong>Double Opt-In:</strong> Subscriptions remain inactive until you explicitly verify ownership by clicking the confirmation link sent by AWS SNS.</li>
          <li><strong>Immediate Unsubscribe:</strong> Every alert notification includes an instantaneous, single-click unsubscribe link.</li>
          <li><strong>Data Isolation:</strong> Email addresses are never shared with marketing platforms, brokers, or external entities.</li>
        </ul>
      </section>
    </article>
  )
}
