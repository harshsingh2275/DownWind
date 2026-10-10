"""Open-Meteo regional weather client and wind field processor for DownWind.

Queries Open-Meteo forecast API across a coarse geographical sampling grid
in a single multi-location HTTP request. Computes directional circular mean
and arithmetic speed mean over a configurable time window, and assigns the
nearest meteorological grid point to fire clusters.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.config import (
    DEFAULT_WIND_WINDOW_HOURS,
    OPEN_METEO_MAX_LOCATIONS,
    WIND_GRID_STEP_DEG,
)
from src.geo import circular_mean_deg, haversine_km

# Open-Meteo forecast endpoint
OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"


class WindError(Exception):
    """Raised when weather API requests or wind field processing fail."""


def build_wind_grid(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    step_deg: float = WIND_GRID_STEP_DEG,
) -> list[tuple[float, float]]:
    """Generate a regular coarse sampling grid of (lat, lon) coordinates.

    Args:
        min_lat: Southernmost latitude bound.
        max_lat: Northernmost latitude bound.
        min_lon: Westernmost longitude bound.
        max_lon: Easternmost longitude bound.
        step_deg: Grid step in degrees.

    Returns:
        List of (lat, lon) coordinate tuples rounded to 4 decimals.
    """
    if step_deg <= 0:
        raise ValueError(f"step_deg must be positive, got {step_deg}")

    points: list[tuple[float, float]] = []
    curr_lat = min_lat
    while curr_lat <= max_lat + 1e-9:
        curr_lon = min_lon
        while curr_lon <= max_lon + 1e-9:
            points.append((round(curr_lat, 4), round(curr_lon, 4)))
            curr_lon += step_deg
        curr_lat += step_deg

    return points


def average_wind(
    hourly_speeds: list[float],
    hourly_dirs: list[float],
    window_hours: int = DEFAULT_WIND_WINDOW_HOURS,
) -> tuple[float, float]:
    """Compute average wind speed and circular average wind direction over a window.

    Wind direction is averaged using circular trigonometry (geo.circular_mean_deg)
    to handle 360°/0° angular wrap-around correctly. Wind speed uses the arithmetic mean.

    Args:
        hourly_speeds: Chronological list of hourly wind speeds in km/h.
        hourly_dirs: Chronological list of hourly wind directions (0-360°).
        window_hours: Number of hourly observations to include from the start.

    Returns:
        Tuple of (average_speed_kmh, average_direction_deg) rounded to 2 decimals.

    Raises:
        ValueError: If speeds or directions are empty, or length mismatch.
    """
    if not hourly_speeds or not hourly_dirs:
        raise ValueError("Cannot average empty wind speed or direction records.")

    if len(hourly_speeds) != len(hourly_dirs):
        raise ValueError("Length mismatch between hourly speeds and hourly directions.")

    speeds = hourly_speeds[:window_hours]
    dirs = hourly_dirs[:window_hours]

    if not speeds:
        raise ValueError("No wind records available within the specified window.")

    avg_speed = sum(speeds) / len(speeds)
    avg_dir = circular_mean_deg(dirs)

    # Compass angles: normalize so 360.0 wraps cleanly to 0.0
    rounded_dir = round(avg_dir, 2) % 360.0

    return round(avg_speed, 2), rounded_dir


def fetch_wind_forecast(
    grid_points: list[tuple[float, float]],
    window_hours: int = DEFAULT_WIND_WINDOW_HOURS,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Execute a single multi-location Open-Meteo forecast request.

    Args:
        grid_points: List of (lat, lon) coordinates to query.
        window_hours: Requested forecast window (used to configure forecast days).
        timeout: Network request timeout in seconds.

    Returns:
        List of location dictionary responses from Open-Meteo.

    Raises:
        ValueError: If grid_points is empty or exceeds OPEN_METEO_MAX_LOCATIONS.
        WindError: If network request or response parsing fails.
    """
    if not grid_points:
        raise ValueError("grid_points cannot be empty.")

    if len(grid_points) > OPEN_METEO_MAX_LOCATIONS:
        raise ValueError(
            f"grid_points count ({len(grid_points)}) exceeds maximum allowed "
            f"({OPEN_METEO_MAX_LOCATIONS})."
        )

    lats = ",".join(str(p[0]) for p in grid_points)
    lons = ",".join(str(p[1]) for p in grid_points)

    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "kmh",
        "forecast_days": "2",
    }
    url = f"{OPEN_METEO_FORECAST_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DownWind/1.0 (+https://github.com/harshsingh2275/DownWind)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes: bytes = resp.read()
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return list(data)
            raise WindError(f"Unexpected JSON response format: {type(data)}")
    except urllib.error.HTTPError as exc:
        raise WindError(f"Open-Meteo HTTP {exc.code} error: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise WindError(f"Open-Meteo network error: {exc.reason}") from exc
    except Exception as exc:
        raise WindError(f"Failed to fetch Open-Meteo forecast: {exc}") from exc


def parse_wind_forecast(
    locations_data: list[dict[str, Any]],
    window_hours: int = DEFAULT_WIND_WINDOW_HOURS,
) -> dict[tuple[float, float], tuple[float, float]]:
    """Parse Open-Meteo multi-location response into a grid wind lookup map.

    Args:
        locations_data: List of location objects from Open-Meteo.
        window_hours: Hours to average over.

    Returns:
        Mapping of (grid_lat, grid_lon) -> (avg_speed_kmh, avg_dir_deg).
    """
    grid_wind_map: dict[tuple[float, float], tuple[float, float]] = {}

    for loc in locations_data:
        if "latitude" not in loc or "longitude" not in loc or "hourly" not in loc:
            continue

        lat = round(float(loc["latitude"]), 4)
        lon = round(float(loc["longitude"]), 4)

        hourly = loc["hourly"]
        speeds_raw = hourly.get("wind_speed_10m", [])
        dirs_raw = hourly.get("wind_direction_10m", [])

        if not speeds_raw or not dirs_raw:
            continue

        speeds = [float(s) for s in speeds_raw]
        dirs = [float(d) for d in dirs_raw]

        avg_speed, avg_dir = average_wind(speeds, dirs, window_hours=window_hours)
        grid_wind_map[(lat, lon)] = (avg_speed, avg_dir)

    return grid_wind_map


def nearest_grid_point(
    lat: float,
    lon: float,
    grid_points: list[tuple[float, float]],
) -> tuple[float, float]:
    """Find the closest meteorological grid point to a given coordinate.

    Uses great-circle distance (haversine_km) for spherical accuracy.

    Args:
        lat: Target latitude in degrees.
        lon: Target longitude in degrees.
        grid_points: Candidate grid coordinates.

    Returns:
        The nearest (grid_lat, grid_lon) tuple.

    Raises:
        ValueError: If grid_points list is empty.
    """
    if not grid_points:
        raise ValueError("grid_points list cannot be empty.")

    nearest = min(grid_points, key=lambda gp: haversine_km(lat, lon, gp[0], gp[1]))
    return nearest


def assign_wind_to_cluster(
    cluster: dict[str, Any],
    grid_wind_map: dict[tuple[float, float], tuple[float, float]],
) -> dict[str, Any]:
    """Assign nearest grid point wind speed and direction to a fire cluster.

    Args:
        cluster: Cluster dictionary with 'lat' and 'lon'.
        grid_wind_map: Mapping of (grid_lat, grid_lon) -> (speed_kmh, dir_deg).

    Returns:
        Updated cluster dictionary containing 'windSpeedKmh', 'windDirDeg',
        and 'windGridPoint'.

    Raises:
        ValueError: If grid_wind_map is empty.
    """
    if not grid_wind_map:
        raise ValueError("grid_wind_map cannot be empty.")

    c_lat = float(cluster.get("lat", cluster.get("centroid", {}).get("lat", 0.0)))
    c_lon = float(cluster.get("lon", cluster.get("centroid", {}).get("lon", 0.0)))

    grid_points = list(grid_wind_map.keys())
    nearest = nearest_grid_point(c_lat, c_lon, grid_points)
    speed, direction = grid_wind_map[nearest]

    cluster["windSpeedKmh"] = speed
    cluster["windDirDeg"] = direction
    cluster["windGridPoint"] = [nearest[0], nearest[1]]

    return cluster
