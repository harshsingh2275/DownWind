import { PRODUCT_NAME } from '../config'

export function PrivacyPage() {
  return (
    <article className="max-w-[64ch] space-y-8">
      {/* Draft Notice per prompt and design.md §8 */}
      <div className="border border-divider bg-surface p-4 text-small space-y-2">
        <span className="font-mono text-accent font-semibold block uppercase">
          Draft, pending review
        </span>
        <p className="text-text-muted m-0 leading-relaxed">
          This document is a preliminary operational draft outlining the privacy practices of {PRODUCT_NAME}.
          It has not been approved by qualified legal counsel and contains placeholder items marked for operator confirmation (Action M-12).
        </p>
      </div>

      <header className="border-b border-divider pb-6">
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Privacy Policy
        </h1>
        <span className="font-mono text-small text-text-muted block mt-2">
          Effective: October 2026 • Status: Draft, pending review • Operator: [OPERATOR_NAME: Pending review (M-12)]
        </span>
      </header>

      {/* 1. Zero Tracking */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Zero Visitor Tracking and Zero Third-Party Analytics
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          {PRODUCT_NAME} is built with data minimization as a core design principle:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-body text-text-muted leading-relaxed">
          <li>No tracking cookies or marketing beacons are set on your device.</li>
          <li>No commercial analytics platforms (such as Google Analytics, Meta Pixel, or Mixpanel) are installed.</li>
          <li>No browser fingerprinting, cross-site profiling, or behavioral tracking is conducted.</li>
          <li>No user registration, passwords, or personal profiles are created.</li>
        </ul>
      </section>

      {/* 2. Self-Hosted Fonts */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. Self-Hosted Typography Assets
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          All font files (Public Sans, IBM Plex Mono, and Noto Sans Devanagari) are bundled directly with the application
          and served from our own hosting origin. Your web browser never contacts third-party font distribution networks
          (such as Google Fonts), preventing your IP address from being logged by third-party font providers.
        </p>
      </section>

      {/* 3. Email Subscriptions & AWS SNS */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. Email Alert Subscriptions and AWS SNS
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          When you subscribe to receive smoke advisories for a monitored city, we process only two data fields:
          your email address and the selected city identifier.
        </p>
        <div className="space-y-2 text-small">
          <div className="border border-divider bg-surface p-3.5 space-y-1">
            <h4 className="font-semibold text-text m-0">No Application Subscriber Database</h4>
            <p className="text-text-muted m-0 leading-relaxed">
              {PRODUCT_NAME} does not maintain an internal database table of subscribers.
              Subscription requests are sent directly to Amazon Web Services Simple Notification Service (AWS SNS)
              topics corresponding to the requested city.
            </p>
          </div>
          <div className="border border-divider bg-surface p-3.5 space-y-1">
            <h4 className="font-semibold text-text m-0">Mandatory Double Opt-In Verification</h4>
            <p className="text-text-muted m-0 leading-relaxed">
              AWS SNS enforces automated double opt-in. An unconfirmed subscription request remains inactive and
              will receive zero alerts until you click the confirmation link sent to your inbox.
              Unconfirmed requests expire and are permanently purged by AWS after 48 hours.
            </p>
          </div>
          <div className="border border-divider bg-surface p-3.5 space-y-1">
            <h4 className="font-semibold text-text m-0">Unsubscribe at Any Time</h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Every notification email dispatched by AWS SNS includes a prominent one-click unsubscribe link.
              Clicking the link instantly removes your address from the topic.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Server Logs & Retention */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          4. Server Logs and Data Retention
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          When accessing the website or API endpoints, standard technical connection metadata is recorded in
          AWS CloudWatch logs (including timestamp, requested endpoint, HTTP status code, and coarse IP address).
        </p>
        <ul className="list-disc pl-5 space-y-1 text-body text-text-muted leading-relaxed">
          <li><strong>Retention Policy:</strong> Server logs in AWS CloudWatch are automatically purged after [DATA_RETENTION_PERIOD: Default 30 days, pending review (M-12)].</li>
          <li><strong>PII Masking:</strong> Plaintext email addresses are masked in error logs (for example, u***@example.com) to prevent exposure of personally identifiable information.</li>
          <li><strong>Security Secrets:</strong> NASA FIRMS access keys and AWS credentials are stored securely in AWS Systems Manager Parameter Store and are never printed in logs or client bundles.</li>
        </ul>
      </section>

      {/* 5. Third-Party Interactions */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          5. Third-Party Service Interactions
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          When viewing the interactive map, your browser directly loads cartographic map tiles from OpenStreetMap
          tile servers (tile.openstreetmap.org). Your IP address and standard browser HTTP headers are received by
          OpenStreetMap in accordance with their standard server operating practices.
        </p>
        <p className="text-body text-text-muted leading-relaxed">
          Air quality baseline metrics are fetched from Open-Meteo. No identifying user data is attached to these queries.
        </p>
      </section>

      {/* 6. Contact and Jurisdiction */}
      <section className="space-y-3 border-t border-divider pt-6">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          6. Operator Information and Privacy Inquiries
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          This platform is operated by [OPERATOR_NAME: Pending review (M-12)], located in [LEGAL_JURISDICTION: Pending review (M-12)].
        </p>
        <p className="text-body text-text-muted leading-relaxed">
          For privacy inquiries, removal requests, or questions regarding this draft policy, contact: [CONTACT_EMAIL: Pending review (M-12)].
        </p>
      </section>
    </article>
  )
}
