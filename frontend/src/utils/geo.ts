/**
 * Geodesy utilities for DownWind frontend (T-056).
 */

/**
 * Calculates downwind smoke travel bearing from meteorological wind-from direction.
 * Wind from 270° (West) blows smoke towards 90° (East).
 */
export function getSmokeBearing(windDirFromDeg: number): number {
  return (windDirFromDeg + 180) % 360
}

/**
 * Great-circle destination point calculation.
 * Computes destination latitude and longitude given start coordinates,
 * bearing in degrees, and distance in kilometers.
 */
export function calculateDestinationPoint(
  lat: number,
  lon: number,
  distanceKm: number,
  bearingDeg: number
): [number, number] {
  const R = 6371 // Earth radius in km
  const dByR = distanceKm / R
  const brgRad = (bearingDeg * Math.PI) / 180
  const latRad = (lat * Math.PI) / 180
  const lonRad = (lon * Math.PI) / 180

  const destLatRad = Math.asin(
    Math.sin(latRad) * Math.cos(dByR) +
      Math.cos(latRad) * Math.sin(dByR) * Math.cos(brgRad)
  )

  const destLonRad =
    lonRad +
    Math.atan2(
      Math.sin(brgRad) * Math.sin(dByR) * Math.cos(latRad),
      Math.cos(dByR) - Math.sin(latRad) * Math.sin(destLatRad)
    )

  return [
    (destLatRad * 180) / Math.PI,
    (destLonRad * 180) / Math.PI,
  ]
}
