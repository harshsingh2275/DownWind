import './App.css'

export default function App() {
  return (
    <div className="min-h-screen bg-bg text-text font-sans p-6 md:p-12">
      <header className="border-b border-divider pb-4 mb-8 flex justify-between items-center">
        <span className="font-mono text-small text-text-muted uppercase tracking-wider">
          Satellite Fire & Smoke Trajectory • Punjab & Haryana
        </span>
        <span className="font-mono text-small text-text-muted">
          06:00 IST
        </span>
      </header>

      <main className="max-w-[1200px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        <div>
          <span className="font-mono text-small text-text-muted block mb-2 uppercase">
            Monitoring Overview
          </span>
          <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight mb-4">
            Fire detections across Punjab and Haryana, and where the smoke may go next
          </h1>
          <p className="text-body text-text-muted mb-8 max-w-[64ch]">
            Near real-time thermal anomaly data tracked alongside atmospheric wind models to map downwind particulate spread across northern India.
          </p>

          <div className="flex flex-wrap gap-4 items-center mb-8">
            <button
              type="button"
              className="bg-accent text-white px-5 py-3 min-h-[44px] hover:bg-accent-hover font-sans text-small border-0 cursor-pointer"
            >
              See the live map
            </button>
            <a
              href="#how-it-works"
              className="text-accent underline hover:text-accent-hover text-small"
            >
              How the estimate works
            </a>
          </div>

          <div className="border border-divider p-4 bg-surface">
            <span className="font-mono text-small text-text-muted block mb-2">
              System Verification (T-051)
            </span>
            <ul className="text-small space-y-1 list-none p-0 m-0 font-mono text-text">
              <li>• border-radius: 0px (enforced globally)</li>
              <li>• Fonts: Public Sans, IBM Plex Mono, Noto Sans Devanagari</li>
              <li>• Accent contrast: 5.37:1 (WCAG AA pass)</li>
              <li>• Accent-mid contrast: 4.89:1 (WCAG AA pass)</li>
            </ul>
          </div>
        </div>

        <div className="border border-divider bg-surface p-6">
          <div className="flex justify-between border-b border-divider pb-2 mb-4">
            <span className="font-mono text-small text-text-muted">
              Map Layout Reference • 29.5°N - 32.0°N
            </span>
            <span className="font-mono text-small text-text-muted">
              WGS 84
            </span>
          </div>
          <div className="h-[260px] bg-bg border border-divider flex items-center justify-center p-4">
            <div className="text-center">
              <span className="font-mono text-data text-accent block mb-1">
                428 Clusters Active
              </span>
              <span className="text-small text-text-muted">
                Interactive Leaflet map container (T-054 target)
              </span>
            </div>
          </div>
          <div className="grid grid-cols-3 border-t border-divider mt-4 pt-4 text-left">
            <div className="pr-4 border-r border-divider">
              <span className="font-mono text-data block text-text">1,842</span>
              <span className="text-small text-text-muted">Active fires (24h)</span>
            </div>
            <div className="px-4 border-r border-divider">
              <span className="font-mono text-data block text-text">14 km/h</span>
              <span className="text-small text-text-muted">NW wind vector</span>
            </div>
            <div className="pl-4">
              <span className="font-mono text-data block text-text">340 km</span>
              <span className="text-small text-text-muted">Plume reach estimate</span>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-divider mt-12 pt-6 flex justify-between items-center text-small text-text-muted font-mono">
        <span>DownWind • Geospatial Fire Telemetry</span>
        <a href="/method" className="text-accent underline">Methodology & Sources</a>
      </footer>
    </div>
  )
}
