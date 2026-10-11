import { PRODUCT_NAME } from '../config'

export function TermsPage() {
  return (
    <article className="max-w-[64ch] space-y-8">
      {/* Draft Notice per prompt and design.md §8 */}
      <div className="border border-divider bg-surface p-4 text-small space-y-2">
        <span className="font-mono text-accent font-semibold block uppercase">
          Draft, pending review
        </span>
        <p className="text-text-muted m-0 leading-relaxed">
          This document is a preliminary operational draft for the non-commercial {PRODUCT_NAME} public interest initiative.
          It has not been approved by qualified legal counsel and contains placeholder items marked for operator confirmation (Action M-12).
        </p>
      </div>

      <header className="border-b border-divider pb-6">
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Terms of Use
        </h1>
        <span className="font-mono text-small text-text-muted block mt-2">
          Effective: October 2026 • Status: Draft, pending review • Jurisdiction: [LEGAL_JURISDICTION: Pending review (M-12)]
        </span>
      </header>

      {/* 1. Purpose */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Public Interest and Educational Purpose
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          {PRODUCT_NAME} is an open, non-commercial public interest tool developed to visualize satellite thermal anomaly telemetry
          and atmospheric wind forecasts for environmental awareness across Punjab and Haryana.
          The platform is operated by [OPERATOR_NAME: Pending review (M-12)].
        </p>
      </section>

      {/* 2. No Atmospheric Guarantee */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. No Guarantee of Atmospheric Accuracy
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          All fire cluster locations, smoke transport corridors, arrival times (ETA), and severity classifications
          provided on this service are automated mathematical heuristics. They are not physical ground truth measurements
          and do not constitute official statutory forecasts, civil defense alerts, or medical advisories.
        </p>
        <p className="text-body text-text-muted leading-relaxed">
          Users must consult statutory government authorities including the Central Pollution Control Board (CPCB),
          India Meteorological Department (IMD), and State Pollution Control Boards for official directives, health warnings,
          and ambient air quality index determinations.
        </p>
      </section>

      {/* 3. Acceptable Use */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. Acceptable Use and Subscription Abuse
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          You agree to use this platform solely for lawful, personal, research, or informational purposes.
          You agree not to:
        </p>
        <ul className="list-disc pl-5 space-y-1.5 text-body text-text-muted leading-relaxed">
          <li>Submit third-party email addresses without authorization to generate unsolicited verification emails.</li>
          <li>Execute automated denial of service attacks, scraping scripts, or flood requests against API endpoints.</li>
          <li>Systematically bulk download map tiles in violation of the OpenStreetMap Tile Usage Policy.</li>
          <li>Misrepresent automated corridor estimates as certified statutory statements from government bodies.</li>
        </ul>
      </section>

      {/* 4. Open Data Attributions */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          4. Data Sources and Intellectual Property
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          {PRODUCT_NAME} incorporates public datasets provided under open licenses:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-small text-text-muted leading-relaxed">
          <li>NASA FIRMS active fire telemetry courtesy of NASA Earthdata.</li>
          <li>Weather forecasts and air quality data courtesy of Open-Meteo.com under Creative Commons Attribution 4.0 International (CC BY 4.0).</li>
          <li>Administrative boundary data courtesy of geoBoundaries under Creative Commons Attribution 4.0 International (CC BY 4.0).</li>
          <li>Map tiles and cartographic data courtesy of OpenStreetMap contributors under the Open Database License (ODbL).</li>
        </ul>
      </section>

      {/* 5. Limitation of Liability */}
      <section className="space-y-3">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          5. Limitation of Liability
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          To the maximum extent permitted by applicable law, the operators, contributors, and authors of {PRODUCT_NAME}
          shall not be liable for any direct, indirect, incidental, consequential, or punitive damages arising from the
          use of, reliance upon, or inability to use the telemetry, maps, notifications, or estimates provided on this site.
        </p>
      </section>

      {/* 6. Jurisdiction & Contact */}
      <section className="space-y-3 border-t border-divider pt-6">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          6. Governing Law and Contact
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          These terms shall be governed by and construed in accordance with the laws of India, subject to the exclusive
          jurisdiction of competent courts in [LEGAL_JURISDICTION: Pending review (M-12)].
        </p>
        <p className="text-body text-text-muted leading-relaxed">
          For queries or concerns regarding these terms, contact: [CONTACT_EMAIL: Pending review (M-12)].
        </p>
      </section>
    </article>
  )
}
