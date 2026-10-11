/**
 * Open-Meteo Air Quality API integration (T-056, FR-08).
 * Fetches current baseline AQI and PM2.5 for monitored urban centers.
 * Labelled strictly as "modelled estimate" per PRD §4 FR-08 & §11.
 */

export interface CityAirQuality {
  cityId: string
  usAqi: number | null
  pm25: number | null
}

interface OpenMeteoItem {
  latitude: number
  longitude: number
  current?: {
    us_aqi?: number
    pm2_5?: number
  }
}

/**
 * Fetch baseline air quality for a list of cities in a single batch request.
 * Free, non-commercial tier Open-Meteo CC BY 4.0.
 */
export async function fetchCitiesAirQuality(
  cities: { id: string; lat: number; lon: number }[]
): Promise<Record<string, CityAirQuality>> {
  if (cities.length === 0) return {}

  const lats = cities.map((c) => c.lat.toFixed(4)).join(',')
  const lons = cities.map((c) => c.lon.toFixed(4)).join(',')
  const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lats}&longitude=${lons}&current=us_aqi,pm2_5`

  const result: Record<string, CityAirQuality> = {}

  try {
    const res = await fetch(url)
    if (!res.ok) {
      // Return empty map on HTTP failure so UI falls back gracefully
      return result
    }

    const data: unknown = await res.json()

    if (Array.isArray(data)) {
      cities.forEach((city, index) => {
        const item = data[index] as OpenMeteoItem | undefined
        result[city.id] = {
          cityId: city.id,
          usAqi: typeof item?.current?.us_aqi === 'number' ? Math.round(item.current.us_aqi) : null,
          pm25: typeof item?.current?.pm2_5 === 'number' ? Math.round(item.current.pm2_5 * 10) / 10 : null,
        }
      })
    } else if (data && typeof data === 'object') {
      const singleItem = data as OpenMeteoItem
      const firstCity = cities[0]
      if (firstCity) {
        result[firstCity.id] = {
          cityId: firstCity.id,
          usAqi: typeof singleItem.current?.us_aqi === 'number' ? Math.round(singleItem.current.us_aqi) : null,
          pm25: typeof singleItem.current?.pm2_5 === 'number' ? Math.round(singleItem.current.pm2_5 * 10) / 10 : null,
        }
      }
    }
  } catch {
    // Non-blocking: air quality service errors do not crash application
  }

  return result
}
