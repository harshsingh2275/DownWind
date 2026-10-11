import React from 'react'
import { PRODUCT_NAME } from '../config'
import { Link } from '../router'
import { useRouter } from '../routerContext'

export function Layout({ children }: { children: React.ReactNode }) {
  const { path } = useRouter()

  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Live Map', href: '/map' },
    { label: 'Daily Report', href: '/report' },
    { label: 'Methodology', href: '/method' },
  ]

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col font-sans">
      {/* 1. Accessible Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:bg-accent focus:text-white focus:px-4 focus:py-2 focus:text-small font-sans focus:outline-none"
      >
        Skip to main content
      </a>

      {/* 2. Semantic Header & Navigation */}
      <header className="border-b border-divider bg-bg sticky top-0 z-40">
        <div className="max-w-[1200px] mx-auto px-4 py-3 md:px-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-h3 font-semibold text-text tracking-tight no-underline hover:text-accent"
            >
              {PRODUCT_NAME}
            </Link>
            <span className="font-mono text-[11px] text-text-muted uppercase border-l border-divider pl-3 hidden sm:inline">
              Punjab & Haryana Corridor
            </span>
          </div>

          <nav aria-label="Main Navigation" className="flex items-center gap-5 sm:gap-6 text-small">
            {navItems.map((item) => {
              const isActive = path === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`no-underline pb-0.5 border-b-2 transition-colors ${
                    isActive
                      ? 'border-accent text-accent font-medium'
                      : 'border-transparent text-text-muted hover:text-text hover:border-divider'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>

      {/* 3. Main Content Container */}
      <main id="main-content" className="flex-1 max-w-[1200px] w-full mx-auto px-4 py-8 md:px-8">
        {children}
      </main>

      {/* 4. Semantic Footer with Required Attributions */}
      <footer className="border-t border-divider bg-surface mt-16 text-small text-text-muted">
        <div className="max-w-[1200px] mx-auto px-4 py-10 md:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 pb-8 border-b border-divider">
            <div>
              <span className="font-mono text-small text-text font-medium block mb-2">
                {PRODUCT_NAME}
              </span>
              <p className="text-small text-text-muted max-w-[50ch] mb-3">
                Near real-time crop residue fire detections across Punjab and Haryana, modeled
                with atmospheric wind vectors to estimate downwind smoke trajectories.
              </p>
              <p className="font-mono text-[12px] text-text-muted">
                Non-commercial public interest initiative. Trajectories are automated mathematical estimates.
              </p>
            </div>

            <div>
              <span className="font-mono text-small text-text font-medium block mb-2">
                Legal & Information
              </span>
              <ul className="list-none p-0 m-0 space-y-1.5 text-small">
                <li>
                  <Link href="/terms" className="text-accent underline hover:text-accent-hover">
                    Terms of Use (Draft)
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="text-accent underline hover:text-accent-hover">
                    Privacy Policy (Draft)
                  </Link>
                </li>
                <li>
                  <Link href="/method" className="text-accent underline hover:text-accent-hover">
                    Methodology & Limitations
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Mandatory Attributions per PRD, architecture.md, and Decision D-019 */}
          <div className="space-y-2 text-[13px] leading-relaxed">
            <span className="font-mono text-[12px] uppercase text-text block mb-1">
              Data Sources & Attributions:
            </span>
            <p className="m-0">
              • Thermal fire anomaly data provided by{' '}
              <a
                href="https://firms.modaps.eosdis.nasa.gov/"
                target="_blank"
                rel="noreferrer"
                className="text-accent underline hover:text-accent-hover"
              >
                NASA FIRMS
              </a>{' '}
              (VIIRS NOAA-20 / NOAA-21 / SNPP, MODIS).
            </p>
            <p className="m-0">
              • Wind vectors and atmospheric forecast data by{' '}
              <a
                href="https://open-meteo.com/"
                target="_blank"
                rel="noreferrer"
                className="text-accent underline hover:text-accent-hover"
              >
                Open-Meteo.com
              </a>{' '}
              licensed under{' '}
              <a
                href="https://creativecommons.org/licenses/by/4.0/"
                target="_blank"
                rel="noreferrer"
                className="text-accent underline hover:text-accent-hover"
              >
                CC BY 4.0
              </a>.
            </p>
            <p className="m-0">
              • Map cartography and geodata ©{' '}
              <a
                href="https://www.openstreetmap.org/copyright"
                target="_blank"
                rel="noreferrer"
                className="text-accent underline hover:text-accent-hover"
              >
                OpenStreetMap contributors
              </a>.
            </p>
            <p className="m-0">
              • Administrative boundary geometries provided by{' '}
              <a
                href="https://www.geoboundaries.org/"
                target="_blank"
                rel="noreferrer"
                className="text-accent underline hover:text-accent-hover"
              >
                geoBoundaries
              </a>{' '}
              licensed under CC BY 4.0 (Runfola et al., 2020).
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
