"""Impact engine for DownWind.

Implements the corridor-based smoke impact algorithm described in
docs/architecture.md §6.  Pure functions only — no I/O, no network.

Algorithm (per architecture §6):
  1. For each (cluster, city) pair:
     a. Get wind speed and wind-from direction for the cluster's nearest grid point.
     b. smoke_bearing = (dir_from + 180) % 360
     c. dist = haversine(cluster → city)
     d. brg  = initial_bearing(cluster → city)
     e. angle_diff = smallest_angle(brg, smoke_bearing)
     f. Affected iff:
        - speed >= MIN_WIND_KMH            (not stagnant, no divide-by-zero)
        - angle_diff <= ANGLE_TOLERANCE_DEG (city is in the smoke corridor)
        - dist <= speed * TRAVEL_HOURS * ATTENUATION  (city is within reach)
     g. eta_hours = dist / speed
  2. Aggregate across all clusters that affect a city:
     nClusters, totalFrp, nearestKm (min dist), minEtaHours (min eta)
  3. Compute severity from totalFrp and minEtaHours using config thresholds.

Severity classification (heuristic, UNVALIDATED — see config.py, D-021, Q-10):
  HIGH   if totalFrp >= SEVERITY_HIGH_FRP   and minEtaHours <= SEVERITY_HIGH_ETA_H
  MEDIUM if totalFrp >= SEVERITY_MEDIUM_FRP and minEtaHours <= SEVERITY_MEDIUM_ETA_H
  LOW    otherwise (any city that is affected at all)
  UI must label all values as "Indicative".
"""

from __future__ import annotations

from typing import Any

from src.config import (
    ANGLE_TOLERANCE_DEG,
    ATTENUATION,
    MIN_WIND_KMH,
    SEVERITY_HIGH_ETA_H,
    SEVERITY_HIGH_FRP,
    SEVERITY_MEDIUM_ETA_H,
    SEVERITY_MEDIUM_FRP,
    TRAVEL_HOURS,
)
from src.geo import (
    haversine_km,
    initial_bearing_deg,
    smallest_angle_diff_deg,
    smoke_bearing_from_wind_from,
)

# Sentinel used internally; not exported
_NO_IMPACT: None = None


def classify_severity(total_frp: float, min_eta_hours: float) -> str:
    """Return indicative severity label for a city's aggregated impact.

    Thresholds are heuristic and UNVALIDATED (see config.py, agents.md D-021, Q-10).
    The UI must always display these values as "Indicative".

    Args:
        total_frp: Sum of FRP (MW) across all affecting clusters.
        min_eta_hours: Minimum estimated travel time in hours across clusters.

    Returns:
        One of "High", "Medium", or "Low".
    """
    if total_frp >= SEVERITY_HIGH_FRP and min_eta_hours <= SEVERITY_HIGH_ETA_H:
        return "High"
    if total_frp >= SEVERITY_MEDIUM_FRP and min_eta_hours <= SEVERITY_MEDIUM_ETA_H:
        return "Medium"
    return "Low"


def compute_cluster_city_impact(
    cluster_lat: float,
    cluster_lon: float,
    cluster_frp: float,
    city_lat: float,
    city_lon: float,
    wind_speed_kmh: float,
    wind_dir_from_deg: float,
) -> dict[str, Any] | None:
    """Test whether a single cluster affects a single city and return impact data.

    Args:
        cluster_lat: Cluster centroid latitude (degrees).
        cluster_lon: Cluster centroid longitude (degrees).
        cluster_frp: Cluster total FRP in MW.
        city_lat: City latitude (degrees).
        city_lon: City longitude (degrees).
        wind_speed_kmh: Wind speed at cluster's nearest grid point (km/h).
        wind_dir_from_deg: Meteorological wind-from direction (degrees, 0-360).

    Returns:
        dict with keys ``dist_km``, ``eta_hours``, ``angle_diff_deg``,
        ``smoke_bearing_deg``, ``bearing_to_city_deg``, ``frp``
        if the city IS affected; ``None`` otherwise.
    """
    # Guard: stagnant wind means no directed plume (also avoids div-by-zero)
    if wind_speed_kmh < MIN_WIND_KMH:
        return _NO_IMPACT

    smoke_bearing = smoke_bearing_from_wind_from(wind_dir_from_deg)
    dist_km = haversine_km(cluster_lat, cluster_lon, city_lat, city_lon)
    bearing_to_city = initial_bearing_deg(cluster_lat, cluster_lon, city_lat, city_lon)
    angle_diff = smallest_angle_diff_deg(bearing_to_city, smoke_bearing)

    # Corridor check
    if angle_diff > ANGLE_TOLERANCE_DEG:
        return _NO_IMPACT

    # Reach check
    max_reach_km = wind_speed_kmh * TRAVEL_HOURS * ATTENUATION
    if dist_km > max_reach_km:
        return _NO_IMPACT

    eta_hours = dist_km / wind_speed_kmh

    return {
        "dist_km": round(dist_km, 3),
        "eta_hours": round(eta_hours, 3),
        "angle_diff_deg": round(angle_diff, 3),
        "smoke_bearing_deg": round(smoke_bearing, 3),
        "bearing_to_city_deg": round(bearing_to_city, 3),
        "frp": cluster_frp,
    }


def compute_impact(
    clusters: list[dict[str, Any]],
    cities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute aggregated smoke impact for each city across all fire clusters.

    Each cluster dict must contain:
      ``lat`` (float), ``lon`` (float), ``totalFrp`` (float),
      ``windSpeedKmh`` (float), ``windDirDeg`` (float).

    Each city dict must contain:
      ``id`` (str), ``name`` (str), ``lat`` (float), ``lon`` (float).

    Args:
        clusters: List of fire cluster dicts (output of clustering + wind assignment).
        cities: List of city dicts (from backend/data/cities.json).

    Returns:
        List of city-impact dicts, one per city that is affected by at least one
        cluster.  Each dict contains:
          - cityId: str
          - cityName: str
          - nClusters: int
          - totalFrp: float (MW)
          - nearestKm: float
          - minEtaHours: float
          - severity: str ("High" | "Medium" | "Low")
          - affectedByClusterIds: list[str]
    """
    # city_id → accumulated impact data
    city_impacts: dict[str, dict[str, Any]] = {}

    for cluster in clusters:
        c_lat = float(cluster.get("lat", cluster.get("centroid", {}).get("lat", 0.0)))
        c_lon = float(cluster.get("lon", cluster.get("centroid", {}).get("lon", 0.0)))
        c_frp = float(cluster.get("totalFrp", 0.0))
        c_id = str(cluster.get("clusterId", ""))
        wind_speed = float(cluster.get("windSpeedKmh", 0.0))
        wind_dir = float(cluster.get("windDirDeg", 0.0))

        for city in cities:
            city_id = str(city.get("id", ""))
            city_lat = float(city.get("lat", 0.0))
            city_lon = float(city.get("lon", 0.0))
            city_name = str(city.get("name", city_id))

            impact = compute_cluster_city_impact(
                cluster_lat=c_lat,
                cluster_lon=c_lon,
                cluster_frp=c_frp,
                city_lat=city_lat,
                city_lon=city_lon,
                wind_speed_kmh=wind_speed,
                wind_dir_from_deg=wind_dir,
            )

            if impact is None:
                continue

            if city_id not in city_impacts:
                city_impacts[city_id] = {
                    "cityId": city_id,
                    "cityName": city_name,
                    "nClusters": 0,
                    "totalFrp": 0.0,
                    "nearestKm": float("inf"),
                    "minEtaHours": float("inf"),
                    "affectedByClusterIds": [],
                }

            acc = city_impacts[city_id]
            acc["nClusters"] += 1
            acc["totalFrp"] = round(acc["totalFrp"] + c_frp, 3)
            if impact["dist_km"] < acc["nearestKm"]:
                acc["nearestKm"] = impact["dist_km"]
            if impact["eta_hours"] < acc["minEtaHours"]:
                acc["minEtaHours"] = impact["eta_hours"]
            if c_id not in acc["affectedByClusterIds"]:
                acc["affectedByClusterIds"].append(c_id)

    # Finalise: round, add severity, sort by severity then nearestKm
    result: list[dict[str, Any]] = []
    severity_order = {"High": 0, "Medium": 1, "Low": 2}

    for acc in city_impacts.values():
        nearest = round(acc["nearestKm"], 3) if acc["nearestKm"] != float("inf") else 0.0
        eta = round(acc["minEtaHours"], 3) if acc["minEtaHours"] != float("inf") else 0.0
        sev = classify_severity(acc["totalFrp"], eta)
        result.append(
            {
                "cityId": acc["cityId"],
                "cityName": acc["cityName"],
                "nClusters": acc["nClusters"],
                "totalFrp": acc["totalFrp"],
                "nearestKm": nearest,
                "minEtaHours": eta,
                "severity": sev,
                "affectedByClusterIds": acc["affectedByClusterIds"],
            }
        )

    result.sort(key=lambda r: (severity_order.get(r["severity"], 9), r["nearestKm"]))
    return result
