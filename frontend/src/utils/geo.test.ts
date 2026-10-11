import { describe, it, expect } from 'vitest'
import { getSmokeBearing, calculateDestinationPoint } from './geo'

describe('geo utilities', () => {
  it('calculates downwind smoke bearing as (wind + 180) % 360', () => {
    // Westerly wind (270°) blows smoke eastward (90°)
    expect(getSmokeBearing(270)).toBe(90)
    // Northerly wind (0°) blows smoke southward (180°)
    expect(getSmokeBearing(0)).toBe(180)
    // Southerly wind (180°) blows smoke northward (0°)
    expect(getSmokeBearing(180)).toBe(0)
    // Easterly wind (90°) blows smoke westward (270°)
    expect(getSmokeBearing(90)).toBe(270)
    // Northwest wind (315°) blows smoke southeast (135°)
    expect(getSmokeBearing(315)).toBe(135)
  })

  it('calculates great circle destination point accurately', () => {
    const startLat = 30.0
    const startLon = 75.0
    const distanceKm = 50.0

    // Heading East (90°)
    const [destLatEast, destLonEast] = calculateDestinationPoint(startLat, startLon, distanceKm, 90)
    expect(destLatEast).toBeCloseTo(30.0, 1)
    expect(destLonEast).toBeGreaterThan(75.0)

    // Heading South (180°)
    const [destLatSouth, destLonSouth] = calculateDestinationPoint(startLat, startLon, distanceKm, 180)
    expect(destLatSouth).toBeLessThan(30.0)
    expect(destLonSouth).toBeCloseTo(75.0, 1)

    // Heading North (0°)
    const [destLatNorth, destLonNorth] = calculateDestinationPoint(startLat, startLon, distanceKm, 0)
    expect(destLatNorth).toBeGreaterThan(30.0)
    expect(destLonNorth).toBeCloseTo(75.0, 1)
  })
})
