import { PRODUCT_NAME } from '../config'

export function TermsPage() {
  return (
    <article className="max-w-[64ch] space-y-8">
      {/* Draft Notice per design.md §8 */}
      <div className="border border-divider bg-surface p-4 text-small">
        <span className="font-mono text-accent font-semibold block uppercase mb-1">
          Notice: Preliminary Draft
        </span>
        <p className="text-text-muted m-0">
          This document is a preliminary operational draft for the non-commercial {PRODUCT_NAME} public interest initiative. It will be reviewed by qualified legal counsel prior to formal production release.
        </p>
      </div>

      <header className="border-b border-divider pb-6">
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Terms of Use
        </h1>
        <span className="font-mono text-small text-text-muted block mt-2">
          Effective: October 2026 • Jurisdiction: India
        </span>
      </header>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Public Interest & Educational Purpose
        </h2>
        <p className="text-body text-text-muted">
          {PRODUCT_NAME} is an open, non-commercial public interest software platform designed to visualize satellite thermal anomaly data and numerical wind predictions for environmental awareness.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. No Guarantee of Atmospheric Accuracy
        </h2>
        <p className="text-body text-text-muted">
          All data feeds, cluster aggregations, smoke plumes, arrival times, and severity classifications provided on this platform are automated mathematical estimates. They do not constitute official statutory forecasts, civil defense warnings, or medical health advisories. Users should consult relevant municipal authorities (CPCB, IMD, State Pollution Control Boards) for formal ambient air quality directives.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. Limitation of Liability
        </h2>
        <p className="text-body text-text-muted">
          Under no circumstances shall the operators, authors, or contributors of {PRODUCT_NAME} be liable for any direct, indirect, incidental, or consequential damages arising from the use of or reliance upon the telemetry, visualizations, or notifications displayed on this platform.
        </p>
      </section>
    </article>
  )
}
