import { useState } from 'react'
import { PRODUCT_NAME } from '../config'

export function ReportPage() {
  const [selectedDay, setSelectedDay] = useState('2024-11-01')

  const handlePrint = () => {
    if (typeof window !== 'undefined') {
      window.print()
    }
  }

  return (
    <div className="space-y-8">
      {/* Report Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-divider pb-6">
        <div>
          <span className="font-mono text-small text-text-muted block mb-1 uppercase tracking-wide">
            Surveillance Telemetry Summary
          </span>
          <h1 className="text-h1-mobile md:text-h1 font-semibold text-text tracking-tight m-0">
            Daily Smoke Impact Report
          </h1>
          <p className="text-body text-text-muted mt-2 max-w-[64ch]">
            Official daily district-level telemetry records for crop residue fires, radiative power, and estimated downwind urban impact.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <input
            type="date"
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="border border-divider bg-bg text-text px-3 py-2 text-small font-mono min-h-[44px] cursor-pointer"
            aria-label="Select report date"
          />
          <button
            type="button"
            onClick={handlePrint}
            className="bg-accent text-white px-5 py-2.5 min-h-[44px] hover:bg-accent-hover font-sans text-small border-0 cursor-pointer print:hidden"
          >
            Print Report
          </button>
        </div>
      </div>

      {/* Printable Report Metadata */}
      <div className="border border-divider bg-surface p-4 flex flex-wrap justify-between gap-4 font-mono text-small">
        <div>
          <span className="text-text-muted block text-[11px] uppercase">Document Title</span>
          <span className="text-text font-medium">{PRODUCT_NAME} Telemetry Summary</span>
        </div>
        <div>
          <span className="text-text-muted block text-[11px] uppercase">Report Date</span>
          <span className="text-text font-medium">{selectedDay} (IST)</span>
        </div>
        <div>
          <span className="text-text-muted block text-[11px] uppercase">Jurisdiction</span>
          <span className="text-text">Punjab & Haryana Surveillance Corridor</span>
        </div>
        <div>
          <span className="text-text-muted block text-[11px] uppercase">Classification</span>
          <span className="text-text">Public / Non-Commercial</span>
        </div>
      </div>

      {/* Table Section */}
      <div className="space-y-4">
        <h2 className="text-h2-mobile md:text-h2 font-semibold text-text m-0">
          City Impact Telemetry
        </h2>
        <div className="overflow-x-auto border border-divider">
          <table className="w-full text-left border-collapse text-small">
            <thead>
              <tr className="bg-surface border-b border-divider text-text font-semibold">
                <th className="p-3">City</th>
                <th className="p-3">State</th>
                <th className="p-3 text-right">Clusters</th>
                <th className="p-3 text-right">Total FRP (MW)</th>
                <th className="p-3 text-right">Nearest (km)</th>
                <th className="p-3 text-right">Est. Arrival (h)</th>
                <th className="p-3">Severity Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-divider font-mono">
              <tr>
                <td className="p-3 font-sans font-medium text-text">Delhi</td>
                <td className="p-3 text-text-muted">Delhi NCR</td>
                <td className="p-3 text-right text-text">14</td>
                <td className="p-3 text-right text-text">484.2</td>
                <td className="p-3 text-right text-text">64.5</td>
                <td className="p-3 text-right text-text">4.2</td>
                <td className="p-3 font-sans">
                  <span className="text-accent font-medium">High</span>
                </td>
              </tr>
              <tr>
                <td className="p-3 font-sans font-medium text-text">Chandigarh</td>
                <td className="p-3 text-text-muted">Chandigarh</td>
                <td className="p-3 text-right text-text">8</td>
                <td className="p-3 text-right text-text">210.0</td>
                <td className="p-3 text-right text-text">32.1</td>
                <td className="p-3 text-right text-text">2.8</td>
                <td className="p-3 font-sans">
                  <span className="text-accent-mid font-medium">Medium</span>
                </td>
              </tr>
              <tr>
                <td className="p-3 font-sans font-medium text-text">Karnal</td>
                <td className="p-3 text-text-muted">Haryana</td>
                <td className="p-3 text-right text-text">5</td>
                <td className="p-3 text-right text-text">95.4</td>
                <td className="p-3 text-right text-text">24.0</td>
                <td className="p-3 text-right text-text">1.9</td>
                <td className="p-3 font-sans">
                  <span className="text-neutral-low font-medium">Low</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-[12px] text-text-muted font-mono mt-2">
          Note: All arrival estimates and severity rankings are automated mathematical estimates based on satellite thermal signatures and numerical wind models.
        </p>
      </div>
    </div>
  )
}
