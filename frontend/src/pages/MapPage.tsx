export function MapPage() {
  return (
    <div className="space-y-6">
      {/* Top Stats Bar */}
      <div className="border border-divider bg-surface p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <div>
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Active Monitoring Day
            </span>
            <span className="font-mono text-data text-text font-medium">
              Today (IST)
            </span>
          </div>
          <div className="border-l border-divider pl-6">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Monitored Corridor
            </span>
            <span className="font-mono text-data text-text">
              Punjab & Haryana
            </span>
          </div>
          <div className="border-l border-divider pl-6 hidden sm:block">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              Data Status
            </span>
            <span className="font-mono text-data text-accent font-medium">
              Near Real-Time Telemetry
            </span>
          </div>
        </div>

        <div className="font-mono text-small text-text-muted">
          Last Updated: <span className="text-text">Live Sync</span>
        </div>
      </div>

      {/* Main Map Application Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left: Interactive Map Container (2/3 width on desktop) */}
        <div className="lg:col-span-2 border border-divider bg-surface p-4 flex flex-col">
          <div className="flex justify-between items-center border-b border-divider pb-3 mb-4">
            <div>
              <h1 className="text-h3 font-semibold text-text m-0">
                Surveillance Map
              </h1>
              <span className="font-mono text-[12px] text-text-muted">
                Satellite fire clusters and estimated smoke trajectory vectors
              </span>
            </div>
            <span className="font-mono text-[12px] bg-bg border border-divider px-2 py-1 text-text-muted">
              WGS 84
            </span>
          </div>

          {/* Interactive Leaflet Map Target Area */}
          <div
            id="map-container"
            className="w-full h-[480px] bg-bg border border-divider flex flex-col items-center justify-center p-6 text-center"
          >
            <span className="font-mono text-small text-accent font-medium mb-2">
              Interactive Map Container (Leaflet T-054)
            </span>
            <p className="text-small text-text-muted max-w-[48ch]">
              High-resolution thermal fire clusters from VIIRS / MODIS sensors rendered as square FRP markers with directional smoke vectors.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-between text-[12px] text-text-muted mt-3 pt-3 border-t border-divider">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 bg-accent inline-block" /> High Severity (&gt;500 MW, &lt;6h)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 bg-accent-mid inline-block" /> Medium Severity (&gt;150 MW, &lt;12h)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 border border-neutral-low inline-block" /> Low Severity
              </span>
            </div>
            <span className="font-mono">OpenStreetMap Attribution Active</span>
          </div>
        </div>

        {/* Right: Cities at Risk & Alert Subscription Panel (1/3 width) */}
        <div className="border border-divider bg-surface p-5 space-y-6">
          <div>
            <h2 className="text-h3 font-semibold text-text mb-1">
              Cities at Risk
            </h2>
            <p className="text-small text-text-muted m-0">
              Downwind smoke arrival estimates based on prevailing wind vectors.
            </p>
          </div>

          <div className="border border-divider bg-bg p-4 space-y-3">
            <span className="font-mono text-[12px] text-text-muted uppercase block">
              Active City Advisories
            </span>
            <p className="text-small text-text-muted m-0">
              Select an urban center to view arrival times, fire radiative power, and active health advisories.
            </p>
          </div>

          {/* Subscribe Box */}
          <div className="border border-divider bg-bg p-4 space-y-3">
            <span className="font-mono text-[12px] text-text-muted uppercase block">
              Email Smoke Alerts
            </span>
            <p className="text-small text-text-muted m-0">
              Receive automated email notifications when high severity smoke trajectories target your city (12h cooldown guard).
            </p>
            <div className="text-[12px] text-text-muted font-mono">
              Double opt-in verified • Zero spam
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
