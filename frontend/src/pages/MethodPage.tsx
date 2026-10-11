import { PRODUCT_NAME } from '../config'

export function MethodPage() {
  return (
    <article className="max-w-[64ch] space-y-10">
      {/* Page Header */}
      <header className="border-b border-divider pb-6">
        <span className="font-mono text-small text-text-muted block mb-1 uppercase tracking-wide">
          Technical Documentation
        </span>
        <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
          Methodology and Data Sources
        </h1>
        <p className="text-body text-text-muted mt-3 leading-relaxed">
          How {PRODUCT_NAME} ingests thermal satellite detections, clusters spatial fire activity,
          evaluates surface wind fields, and calculates heuristic downwind smoke transport corridors across northern India.
        </p>
      </header>

      {/* 1. Data Sources Section */}
      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          1. Data Sources
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          {PRODUCT_NAME} relies on four primary external open data providers:
        </p>

        <div className="space-y-4 text-small">
          <div className="border border-divider bg-surface p-4 space-y-2">
            <h3 className="text-h3 font-semibold text-text m-0">
              NASA FIRMS (Fire Information for Resource Management System)
            </h3>
            <p className="text-text-muted m-0 leading-relaxed">
              Active fire and thermal anomaly telemetry is fetched through the NASA FIRMS Area API.
              The system processes Near Real-Time (NRT) feeds from the Visible Infrared Imaging
              Radiometer Suite (VIIRS) aboard the Suomi NPP, NOAA-20, and NOAA-21 satellites (375-meter resolution),
              alongside Moderate Resolution Imaging Spectroradiometer (MODIS) sensors aboard Terra and Aqua (1-kilometer resolution).
              For historical season dates, standard processing archive feeds (VIIRS_NOAA20_SP) are used.
            </p>
            <p className="text-text-muted m-0 font-mono text-[11px]">
              Attributes ingested: Latitude, longitude, UTC acquisition time, confidence level, and Fire Radiative Power (FRP, measured in MW).
            </p>
          </div>

          <div className="border border-divider bg-surface p-4 space-y-2">
            <h3 className="text-h3 font-semibold text-text m-0">
              Open-Meteo Weather Forecast and Historical Archive
            </h3>
            <p className="text-text-muted m-0 leading-relaxed">
              Surface wind vectors at 10 meters above ground level (wind speed in km/h and meteorological
              wind direction in degrees from north) are retrieved across a coarse spatial grid via the
              Open-Meteo API. Historical archive endpoints are queried for past observations.
              Directional wind averaging across grid points uses circular mean calculations to prevent
              boundary errors when angles wrap around 360 degrees.
            </p>
            <p className="text-text-muted m-0 font-mono text-[11px]">
              Attribution: Weather data by Open-Meteo.com under Creative Commons Attribution 4.0 International (CC BY 4.0).
            </p>
          </div>

          <div className="border border-divider bg-surface p-4 space-y-2">
            <h3 className="text-h3 font-semibold text-text m-0">
              Open-Meteo Air Quality API
            </h3>
            <p className="text-text-muted m-0 leading-relaxed">
              Baseline ambient particulate matter (PM2.5) and US Air Quality Index (AQI) values for monitored
              urban centers are queried from the Open-Meteo Air Quality API. These figures represent
              numerical atmospheric model outputs and are strictly labelled as modelled estimates.
            </p>
          </div>

          <div className="border border-divider bg-surface p-4 space-y-2">
            <h3 className="text-h3 font-semibold text-text m-0">
              geoBoundaries and OpenStreetMap
            </h3>
            <p className="text-text-muted m-0 leading-relaxed">
              Administrative state boundaries for Punjab and Haryana are sourced from geoBoundaries ADM1
              (CC BY 4.0). Basemap tiles are served using OpenStreetMap contributors data (ODbL / CC BY-SA).
            </p>
          </div>
        </div>
      </section>

      {/* 2. Update Frequency Section */}
      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          2. Pipeline Architecture and Update Frequency
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          The ingestion pipeline runs as a scheduled serverless function on AWS Lambda:
        </p>
        <ul className="list-disc pl-5 space-y-2 text-body text-text-muted leading-relaxed">
          <li>
            <strong>Schedule:</strong> Triggered automatically every 30 minutes through an Amazon EventBridge cron rule (rate of 30 minutes).
          </li>
          <li>
            <strong>Data Ingestion:</strong> Each run queries the NASA FIRMS Area API for new thermal anomaly detections within the target bounding box.
          </li>
          <li>
            <strong>Region Filtering:</strong> Raw detections are filtered through a point-in-polygon algorithm against the simplified administrative boundaries of Punjab (ISO code IN-PB) and Haryana (ISO code IN-HR). Detections outside these two states or across international borders are discarded. Low confidence detections are also stripped out.
          </li>
          <li>
            <strong>Storage and Caching:</strong> Formed clusters and computed city impacts are written idempotently to Amazon DynamoDB tables with a 7-day Time To Live (TTL). API Gateway caches static city lists for 300 seconds and dynamic telemetry for 60 seconds.
          </li>
        </ul>
      </section>

      {/* 3. Smoke Estimation Algorithm Section */}
      <section className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          3. How the Smoke Transport Estimate is Made
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          The downwind impact calculation is a deterministic geometric algorithm executed in five stages:
        </p>

        <div className="space-y-4 text-small">
          <div className="border-l-2 border-accent pl-4 space-y-1">
            <h4 className="font-semibold text-text m-0 text-body">
              Stage 1: Spatial Grid Clustering (0.05 Degree Grid)
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Filtered detections are mapped to a 0.05 degree spatial grid (approximately 5.5 km resolution).
              Detections falling within the same grid cell are aggregated into a single cluster.
              The cluster center is calculated as an FRP-weighted centroid, ensuring the cluster coordinate
              aligns with the peak thermal intensity rather than a geometric midpoint.
            </p>
          </div>

          <div className="border-l-2 border-accent pl-4 space-y-1">
            <h4 className="font-semibold text-text m-0 text-body">
              Stage 2: Wind Vector Assignment
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Each cluster centroid is assigned the surface wind speed and wind direction from the nearest
              coarse weather grid point. If wind speed is below 2.0 km/h, the atmosphere is considered
              stagnant and no directional smoke vector is projected.
            </p>
          </div>

          <div className="border-l-2 border-accent pl-4 space-y-1">
            <h4 className="font-semibold text-text m-0 text-body">
              Stage 3: Downwind Smoke Direction
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Meteorological wind direction denotes where the wind is coming from.
              The downwind smoke travel heading is calculated as the reciprocal angle:
              (wind direction + 180 degrees) modulo 360 degrees.
            </p>
          </div>

          <div className="border-l-2 border-accent pl-4 space-y-1">
            <h4 className="font-semibold text-text m-0 text-body">
              Stage 4: Corridor and Reach Verification
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              For every pair of fire cluster and monitored city:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-text-muted m-0">
              <li>Distance is computed using the great-circle Haversine formula.</li>
              <li>Initial bearing from the cluster to the city is computed using spherical trigonometry.</li>
              <li>The angular difference between the smoke vector and the city bearing is calculated.</li>
              <li>A city is marked inside the corridor if the angular difference is 25 degrees or less (half-width tolerance).</li>
              <li>A city is marked within reach if distance is less than or equal to (wind speed * 12 hours * 0.85 attenuation factor).</li>
              <li>Estimated Time of Arrival (ETA) is computed as distance divided by wind speed.</li>
            </ul>
          </div>

          <div className="border-l-2 border-accent pl-4 space-y-1">
            <h4 className="font-semibold text-text m-0 text-body">
              Stage 5: Aggregation and Severity Classification
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              All clusters affecting a city are aggregated to determine total radiative power (MW),
              minimum arrival time (ETA in hours), nearest distance (km), and contributing cluster counts.
              Indicative severity is classified using heuristic thresholds:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-text-muted m-0">
              <li><strong>High Severity:</strong> Total FRP &gt;= 500 MW and minimum ETA &lt;= 6 hours. Triggers automated email notification subject to a 12-hour per-city cooldown.</li>
              <li><strong>Medium Severity:</strong> Total FRP &gt;= 150 MW and minimum ETA &lt;= 12 hours.</li>
              <li><strong>Low Severity:</strong> Any other city within a valid corridor.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* 4. Known Limitations Section (PRD Section 11) */}
      <section className="space-y-4 border-t border-divider pt-8">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text">
          4. Known Scientific and Operational Limitations
        </h2>
        <p className="text-body text-text-muted leading-relaxed">
          In adherence to strict transparency, users and researchers must take note of the following limitations:
        </p>

        <div className="border border-divider bg-surface p-5 space-y-4 text-small text-text">
          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Thermal Anomalies vs Confirmed Crop Burns
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              NASA FIRMS registers satellite thermal anomalies. While the overwhelming majority of seasonal
              detections in rural Punjab and Haryana during October and November correspond to crop residue burning,
              satellites also detect other thermal heat sources such as industrial boilers, brick kilns, and non-crop fires.
              {PRODUCT_NAME} labels detections as possible crop-residue fires or fire detections, not confirmed stubble burning.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Satellite Orbit Intervals and Latency
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Satellites do not hover continuously over northern India. They cross the region during scheduled orbital
              passes (typically twice daily for MODIS and twice daily for each VIIRS platform). Consequently, detection
              records represent snapshots in time and are near real-time, not continuous instant telemetry.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Cloud Cover and Smog Obscuration
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Thick cloud cover, heavy fog, or extreme atmospheric smoke layers can attenuate infrared radiation,
              preventing satellite sensors from capturing active ground fires during overcast weather.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Heuristic Corridor vs Numerical Dispersion Models
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              The smoke transport corridor is an automated 2D geometric heuristic based on surface layer wind velocity.
              It is not a 3D Eulerian or Lagrangian chemical dispersion model (such as HYSPLIT or CMAQ).
              It does not account for planetary boundary layer height, vertical thermal plume injection height,
              micro-topography, atmospheric turbulence, chemical aerosol formation, or rain washout.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Modelled Air Quality vs Ground Monitoring Stations
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Baseline Air Quality Index (AQI) values displayed for monitored cities are numerical model outputs
              from Open-Meteo, not physical sensor readings from continuous ambient air quality monitoring
              stations (CAAQMS) operated by the Central Pollution Control Board (CPCB).
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Unvalidated Heuristic Thresholds
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Severity cutoffs (500 MW for High, 150 MW for Medium), corridor angle tolerance (25 degrees),
              and the reach attenuation coefficient (0.85) are operational engineering heuristics.
              They have not been experimentally calibrated against empirical ground particulate data and are labelled indicative.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-text m-0 mb-1">
              • Geographic Boundary Scope
            </h4>
            <p className="text-text-muted m-0 leading-relaxed">
              Surveillance processing is strictly confined to the administrative boundaries of Punjab and Haryana.
              Fires in neighboring Indian states, neighboring countries, or regions outside this boundary polygon
              are excluded from cluster aggregation.
            </p>
          </div>
        </div>
      </section>
    </article>
  )
}
