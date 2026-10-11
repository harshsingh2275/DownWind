/**
 * Global application configuration.
 * Single source of truth for product branding (T-052).
 */
export const PRODUCT_NAME = 'DownWind'
export const PRODUCT_TAGLINE =
  'Fire detections across Punjab and Haryana, and where the smoke may go next'
export const DEFAULT_REGION_NAME = 'Punjab & Haryana'

/**
 * Map Tile Layer Configuration (T-054, TD-002).
 * Default: OpenStreetMap standard tiles with official attribution.
 * Parameterized via environment variables (VITE_TILE_URL, VITE_TILE_ATTRIBUTION)
 * to allow seamless migration to Carto/Protomaps per Q-07 and TD-002.
 */
export const DEFAULT_TILE_URL =
  (import.meta.env.VITE_TILE_URL as string | undefined) ||
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

export const DEFAULT_TILE_ATTRIBUTION =
  (import.meta.env.VITE_TILE_ATTRIBUTION as string | undefined) ||
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'

/** Default map center focused on Punjab & Haryana stubble burning corridor */
export const DEFAULT_MAP_CENTER: [number, number] = [30.5, 75.8]
export const DEFAULT_MAP_ZOOM = 7

