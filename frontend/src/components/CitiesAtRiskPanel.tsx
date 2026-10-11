import { useState, useId } from 'react'
import type { Impact } from '../types/api'
import type { CityAirQuality } from '../api/airQuality'

export interface CitiesAtRiskPanelProps {
  impacts: Impact[]
  airQualityMap?: Record<string, CityAirQuality>
  selectedCityId?: string | null
  onSelectCity?: (cityId: string) => void
  isLoading?: boolean
  className?: string
}

function formatEta(hours: number): string {
  if (hours <= 0) return 'Immediate'
  if (hours < 1) {
    const mins = Math.round(hours * 60)
    return `${mins}m`
  }
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function getAqiCategory(aqi: number): { label: string; textClass: string } {
  if (aqi <= 50) return { label: 'Good', textClass: 'text-text' }
  if (aqi <= 100) return { label: 'Moderate', textClass: 'text-text' }
  if (aqi <= 200) return { label: 'Unhealthy', textClass: 'text-accent-mid' }
  if (aqi <= 300) return { label: 'Very Unhealthy', textClass: 'text-accent' }
  return { label: 'Hazardous', textClass: 'text-accent' }
}

export function CitiesAtRiskPanel({
  impacts,
  airQualityMap = {},
  selectedCityId,
  onSelectCity,
  isLoading = false,
  className = '',
}: CitiesAtRiskPanelProps) {
  const [filterSeverity, setFilterSeverity] = useState<'All' | 'High' | 'Medium' | 'Low'>('All')
  const panelHeadingId = useId()

  const filteredImpacts = filterSeverity === 'All'
    ? impacts
    : impacts.filter((i) => i.severity === filterSeverity)

  return (
    <section
      className={`border border-divider bg-surface p-5 space-y-4 ${className}`}
      aria-labelledby={panelHeadingId}
    >
      <div className="border-b border-divider pb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 id={panelHeadingId} className="text-h3 font-semibold text-text m-0">
            Cities at Risk
          </h2>
          <span className="font-mono text-[11px] text-text-muted block">
            Downwind smoke arrival estimates based on wind vectors
          </span>
        </div>
        <span className="font-mono text-[12px] bg-bg border border-divider px-2 py-0.5 text-text-muted">
          {impacts.length} {impacts.length === 1 ? 'City' : 'Cities'} Monitored
        </span>
      </div>

      {/* Severity Filter Filter Bar */}
      {impacts.length > 0 && (
        <div
          className="flex flex-wrap items-center gap-2 text-[12px]"
          role="toolbar"
          aria-label="Filter cities by severity"
        >
          <span className="font-mono text-[11px] text-text-muted uppercase">Filter:</span>
          {(['All', 'High', 'Medium', 'Low'] as const).map((sev) => {
            const count = sev === 'All' ? impacts.length : impacts.filter((i) => i.severity === sev).length
            const isActive = filterSeverity === sev
            return (
              <button
                key={sev}
                type="button"
                onClick={() => setFilterSeverity(sev)}
                aria-pressed={isActive}
                className={`px-2 py-1 font-mono text-[11px] border transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-text text-white border-text font-medium'
                    : 'bg-bg hover:bg-hover text-text border-divider'
                }`}
              >
                {sev} ({count})
              </button>
            )
          })}
        </div>
      )}

      {/* Async Loading Skeleton */}
      {isLoading && (
        <div className="space-y-3 py-2" aria-busy="true" aria-label="Loading cities at risk telemetry">
          <div className="h-16 bg-divider/40 animate-pulse border border-divider" />
          <div className="h-16 bg-divider/40 animate-pulse border border-divider" />
          <div className="h-16 bg-divider/40 animate-pulse border border-divider" />
        </div>
      )}

      {/* Empty State when no cities impacted */}
      {!isLoading && impacts.length === 0 && (
        <div className="border border-divider bg-bg p-4 text-center space-y-2">
          <p className="text-small text-text font-medium m-0">
            No cities currently in downwind smoke path.
          </p>
          <p className="text-[12px] text-text-muted m-0">
            Active wind vectors do not currently direct fire plumes toward monitored urban centers.
          </p>
        </div>
      )}

      {/* Filter empty state */}
      {!isLoading && impacts.length > 0 && filteredImpacts.length === 0 && (
        <div className="border border-divider bg-bg p-4 text-center">
          <p className="text-small text-text-muted m-0">
            No cities match the {filterSeverity} severity filter.
          </p>
        </div>
      )}

      {/* Cities List */}
      {!isLoading && filteredImpacts.length > 0 && (
        <div
          className="space-y-3 divide-y divide-divider"
          role="list"
          aria-label="Monitored urban centers at risk"
        >
          {filteredImpacts.map((cityImpact) => {
            const isSelected = cityImpact.cityId === selectedCityId
            const aq = airQualityMap[cityImpact.cityId]
            const aqiValue = aq?.usAqi ?? null
            const aqiMeta = aqiValue !== null ? getAqiCategory(aqiValue) : null

            return (
              <div
                key={cityImpact.cityId}
                role="listitem"
                tabIndex={0}
                onClick={() => onSelectCity?.(cityImpact.cityId)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSelectCity?.(cityImpact.cityId)
                  }
                }}
                aria-label={`${cityImpact.cityName}: Severity ${cityImpact.severity}, ETA ${formatEta(cityImpact.minEtaHours)}, Baseline AQI ${aqiValue ?? 'unknown'} modelled estimate`}
                className={`pt-3 first:pt-0 cursor-pointer p-3 border transition-colors ${
                  isSelected
                    ? 'border-focus bg-hover'
                    : 'border-transparent hover:border-divider hover:bg-hover/60 bg-bg'
                }`}
              >
                {/* Header row: City Name + Severity Text Label */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-text text-body">
                      {cityImpact.cityName}
                    </span>
                    <span className="font-mono text-[11px] text-text-muted">
                      ({cityImpact.nearestKm.toFixed(0)} km away)
                    </span>
                  </div>

                  {/* Explicit Severity Text Label */}
                  <span
                    className={`font-mono text-[11px] font-semibold px-2 py-0.5 border ${
                      cityImpact.severity === 'High'
                        ? 'bg-accent text-white border-accent'
                        : cityImpact.severity === 'Medium'
                          ? 'bg-accent-mid text-white border-accent-mid'
                          : 'bg-transparent text-neutral-low border-neutral-low'
                    }`}
                  >
                    {`${cityImpact.severity} Severity`}
                  </span>
                </div>

                {/* Metrics Grid: ETA, Total FRP, Baseline AQI */}
                <div className="grid grid-cols-3 gap-2 text-small border-t border-divider/60 pt-2 font-mono">
                  {/* ETA */}
                  <div>
                    <span className="text-text-muted text-[11px] block font-sans">
                      Estimated ETA
                    </span>
                    <span className="font-semibold text-text text-data">
                      {formatEta(cityImpact.minEtaHours)}
                    </span>
                  </div>

                  {/* Impact FRP */}
                  <div>
                    <span className="text-text-muted text-[11px] block font-sans">
                      Impact Power
                    </span>
                    <span className="font-semibold text-accent text-data">
                      {cityImpact.totalFrp.toFixed(1)} MW
                    </span>
                  </div>

                  {/* Baseline AQI with exact "modelled estimate" label */}
                  <div>
                    <span className="text-text-muted text-[11px] block font-sans">
                      Baseline AQI
                    </span>
                    {aqiValue !== null ? (
                      <div>
                        <span className={`font-semibold text-data ${aqiMeta?.textClass || 'text-text'}`}>
                          {aqiValue}
                        </span>
                        <span className="text-[10px] text-text-muted block font-sans lowercase leading-tight">
                          modelled estimate
                        </span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-text-muted block font-sans">
                        modelled estimate
                      </span>
                    )}
                  </div>
                </div>

                {/* Contributing clusters metadata */}
                <div className="mt-2 text-[11px] text-text-muted flex justify-between items-center border-t border-divider/40 pt-1.5 font-mono">
                  <span>
                    Clusters affecting: <strong className="text-text">{cityImpact.nClusters}</strong>
                  </span>
                  <span className="text-[10px]">
                    Heuristic corridor
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Methodological honest disclaimer per PRD §11 */}
      <div className="border-t border-divider pt-3 text-[11px] text-text-muted font-mono leading-relaxed space-y-1">
        <p className="m-0">
          • Baseline AQI: Open-Meteo European/US air quality (<span className="text-text font-medium">modelled estimate</span>, not ground monitor reading).
        </p>
        <p className="m-0">
          • Severity and ETA: Heuristic corridor calculations (<span className="text-text font-medium">indicative</span>).
        </p>
      </div>
    </section>
  )
}
