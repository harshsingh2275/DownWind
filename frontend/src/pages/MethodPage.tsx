import { PRODUCT_NAME } from '../config'

export function MethodPage() {
  return (
    <article className="max-w-[64ch] space-y-8">
      <header className="border-b border-divider pb-6">
        <span className="font-mono text-small text-text-muted block mb-1 uppercase tracking-wide">
          Technical Documentation
        </span>
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Methodology & Data Limitations
        </h1>
        <p className="text-body text-text-muted mt-3">
          How {PRODUCT_NAME} ingests thermal satellite telemetry, calculates spatial fire clusters,
          and models downwind smoke transport corridors across northern India.
        </p>
      </header>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Satellite Fire Detection (NASA FIRMS)
        </h2>
        <p className="text-body text-text-muted">
          Active thermal fire telemetry is retrieved from the NASA Fire Information for Resource
          Management System (FIRMS) Area API using the VIIRS (Visible Infrared Imaging Radiometer
          Suite) sensors aboard the Suomi NPP, NOAA-20, and NOAA-21 satellite constellations.
        </p>
        <p className="text-body text-text-muted">
          Thermal detections provide pixel-level latitude, longitude, acquisition timestamp (converted
          to Indian Standard Time), confidence level, and Fire Radiative Power (FRP, measured in megawatts).
          Detections with low confidence are systematically discarded to eliminate false positives.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. Spatial Grid Clustering
        </h2>
        <p className="text-body text-text-muted">
          Individual 375m satellite detections are grouped into deterministic spatial grid cells
          of 0.05° resolution (approximately 5.5 km). Each resulting cluster is assigned:
        </p>
        <ul className="list-disc pl-5 space-y-2 text-body text-text-muted">
          <li>A Fire Radiative Power weighted centroid representing the true thermal core of the fire activity.</li>
          <li>Aggregate cluster fire count and total radiative energy (MW).</li>
          <li>First seen and most recent acquisition timestamps for the current monitoring day.</li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. Wind Vector Modeling & Downwind Corridors
        </h2>
        <p className="text-body text-text-muted">
          Atmospheric surface wind speed and wind direction (at 10m height) are retrieved from
          Open-Meteo numerical weather prediction models. For each cluster:
        </p>
        <ul className="list-disc pl-5 space-y-2 text-body text-text-muted">
          <li>The smoke transport bearing is derived as the reciprocal direction of the wind origin vector.</li>
          <li>The angle difference between the smoke vector and target urban centers is computed using spherical trigonometry (haversine and initial bearing formulas).</li>
          <li>Cities within a 25° corridor half-width and within travel distance horizons are evaluated for smoke impact.</li>
          <li>Estimated time of arrival (ETA) is computed based on distance and prevailing transport speed.</li>
        </ul>
      </section>

      <section className="space-y-4 border-t border-divider pt-6">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          4. Known Scientific Limitations
        </h2>
        <div className="border border-divider bg-surface p-4 text-small space-y-2 text-text">
          <p className="m-0 font-medium">Please note the following critical limitations:</p>
          <ul className="list-disc pl-5 space-y-1 text-text-muted m-0">
            <li><strong>Thermal Anomaly Classification:</strong> Satellite detections indicate thermal anomalies, which are predominantly agricultural crop residue burns during harvest season, but can occasionally represent industrial furnaces or non-agricultural fires.</li>
            <li><strong>Cloud Cover Obstruction:</strong> Heavy cloud cover or dense fog can obstruct optical satellite sensors, resulting in under-counting during overcast conditions.</li>
            <li><strong>Model Heuristics:</strong> Smoke arrival times and corridors are automated mathematical estimates based on 2D surface wind fields; micro-topography, atmospheric boundary layer mixing, and secondary particulate formation are not modeled.</li>
          </ul>
        </div>
      </section>
    </article>
  )
}
