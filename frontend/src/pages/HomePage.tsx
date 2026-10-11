import { PRODUCT_TAGLINE } from '../config'
import { Link } from '../router'

export function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        <div>
          <span className="font-mono text-small text-text-muted block mb-2 uppercase tracking-wide">
            Monitoring Overview • Punjab & Haryana
          </span>
          <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight mb-4">
            {PRODUCT_TAGLINE}
          </h1>
          <p className="text-body text-text-muted mb-8 max-w-[64ch]">
            Satellite fire telemetry updated through the day alongside atmospheric wind forecasts.
            Select your city and track estimated downwind smoke trajectories.
          </p>

          <div className="flex flex-wrap gap-4 items-center">
            <Link
              href="/map"
              className="bg-accent text-white px-5 py-3 min-h-[44px] hover:bg-accent-hover font-sans text-small no-underline inline-flex items-center justify-center border-0 cursor-pointer"
            >
              See the live map
            </Link>
            <Link
              href="/method"
              className="text-accent underline hover:text-accent-hover text-small"
            >
              How the estimate works
            </Link>
          </div>
        </div>

        {/* Live Map Preview Container (0px radius) */}
        <div className="border border-divider bg-surface p-6">
          <div className="flex justify-between items-center border-b border-divider pb-2 mb-4">
            <span className="font-mono text-small text-text-muted">
              Live Surveillance Corridor • 29.5°N - 32.0°N
            </span>
            <span className="font-mono text-small text-text-muted">
              WGS 84
            </span>
          </div>

          <div className="h-[260px] bg-bg border border-divider flex flex-col items-center justify-center p-6 text-center">
            <span className="font-mono text-small text-accent font-medium mb-1">
              Active Satellite & Wind Model
            </span>
            <p className="text-small text-text-muted max-w-[40ch] mb-4">
              Real-time cluster aggregation and trajectory vectors are computed from NASA FIRMS telemetry and Open-Meteo wind forecasts.
            </p>
            <Link
              href="/map"
              className="text-accent underline text-small font-medium"
            >
              Open Full Interactive Map →
            </Link>
          </div>

          <div className="grid grid-cols-3 border-t border-divider mt-4 pt-4 text-left">
            <div className="pr-4 border-r border-divider">
              <span className="font-mono text-data block text-text">15 Cities</span>
              <span className="text-[12px] text-text-muted">Monitored urban centers</span>
            </div>
            <div className="px-4 border-r border-divider">
              <span className="font-mono text-data block text-text">30 min</span>
              <span className="text-[12px] text-text-muted">Ingest frequency</span>
            </div>
            <div className="pl-4">
              <span className="font-mono text-data block text-text">12 h</span>
              <span className="text-[12px] text-text-muted">Alert cooldown guard</span>
            </div>
          </div>
        </div>
      </section>

      {/* How the Estimate Works (Numbered vertical list per design.md §8) */}
      <section className="border-t border-divider pt-12 max-w-[64ch]">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text mb-6">
          How the estimate works
        </h2>

        <ol className="list-none p-0 m-0 space-y-6">
          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              01 • Thermal anomaly detection
            </span>
            <p className="text-body text-text-muted m-0">
              NASA FIRMS satellites (VIIRS 375m sensor) detect active heat signatures across the agricultural corridor of Punjab and Haryana in near real-time.
            </p>
          </li>

          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              02 • Spatial clustering & intensity
            </span>
            <p className="text-body text-text-muted m-0">
              Nearby fire detections within 0.05° grid cells are clustered into aggregated burn centers with fire radiative power (FRP) weighted centroids.
            </p>
          </li>

          <li className="border-l-2 border-accent pl-4">
            <span className="font-mono text-small text-accent font-medium block mb-1">
              03 • Atmospheric wind vector modeling
            </span>
            <p className="text-body text-text-muted m-0">
              High-resolution hourly surface wind data from Open-Meteo determines downwind smoke trajectory corridors, arrival time estimates (ETA), and city risk severity.
            </p>
          </li>
        </ol>
      </section>
    </div>
  )
}
