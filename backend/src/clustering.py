"""Spatial grid-based fire detection clustering for DownWind.

Aggregates individual satellite fire detections into spatial grid clusters
using the configured CLUSTER_GRID_DEG. Computes FRP-weighted centroid,
fire count, total FRP, maximum FRP, and temporal bounds (firstSeen, lastSeen)
with deterministic cluster IDs.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from src.config import CLUSTER_GRID_DEG


def get_grid_cell_id(lat: float, lon: float, grid_deg: float = CLUSTER_GRID_DEG) -> str:
    """Generate a deterministic string ID for a grid cell.

    Args:
        lat: Latitude of the point in degrees.
        lon: Longitude of the point in degrees.
        grid_deg: Cell size in degrees (defaults to CLUSTER_GRID_DEG).

    Returns:
        Deterministic identifier formatted as '<base_lat>_<base_lon>'.
    """
    lat_idx = math.floor(lat / grid_deg)
    lon_idx = math.floor(lon / grid_deg)
    base_lat = round(lat_idx * grid_deg, 4)
    base_lon = round(lon_idx * grid_deg, 4)
    return f"{base_lat:.4f}_{base_lon:.4f}"


def cluster_detections(
    detections: list[dict[str, Any]],
    grid_deg: float = CLUSTER_GRID_DEG,
) -> list[dict[str, Any]]:
    """Cluster raw fire detections into spatial grid cells.

    Centroid is computed using Fire Radiative Power (FRP) weighting when
    totalFrp > 0; falls back to simple arithmetic mean when totalFrp is 0.

    Args:
        detections: List of detection dictionaries containing 'lat'/'latitude',
                    'lon'/'longitude', 'frp', and 'acq_utc'.
        grid_deg: Spatial cell resolution in degrees.

    Returns:
        Sorted list of cluster dictionaries containing:
        - clusterId: Deterministic grid cell key
        - centroid: dict with 'lat' and 'lon'
        - lat: float centroid latitude
        - lon: float centroid longitude
        - count: int number of detections in cluster
        - totalFrp: float sum of FRP across cluster (rounded to 2 decimals)
        - maxFrp: float maximum FRP among cluster detections
        - firstSeen: ISO 8601 UTC timestamp of earliest detection
        - lastSeen: ISO 8601 UTC timestamp of latest detection
        - firstSeenUtc: ISO 8601 UTC timestamp
        - lastSeenUtc: ISO 8601 UTC timestamp
    """
    if not detections:
        return []

    # Group detections by cell ID
    cells: dict[str, list[dict[str, Any]]] = {}
    for det in detections:
        lat = float(det.get("lat", det.get("latitude", 0.0)))
        lon = float(det.get("lon", det.get("longitude", 0.0)))
        cid = get_grid_cell_id(lat, lon, grid_deg)
        cells.setdefault(cid, []).append(det)

    clusters: list[dict[str, Any]] = []

    for cid in sorted(cells.keys()):
        cell_points = cells[cid]
        count = len(cell_points)

        total_frp = 0.0
        max_frp = 0.0
        weighted_lat_sum = 0.0
        weighted_lon_sum = 0.0
        simple_lat_sum = 0.0
        simple_lon_sum = 0.0

        timestamps: list[datetime] = []

        for p in cell_points:
            lat = float(p.get("lat", p.get("latitude", 0.0)))
            lon = float(p.get("lon", p.get("longitude", 0.0)))
            frp = float(p.get("frp", 0.0))

            simple_lat_sum += lat
            simple_lon_sum += lon
            weighted_lat_sum += lat * frp
            weighted_lon_sum += lon * frp

            total_frp += frp
            if frp > max_frp:
                max_frp = frp

            ts_raw = p.get("acq_utc")
            if isinstance(ts_raw, datetime):
                timestamps.append(ts_raw)
            elif isinstance(ts_raw, str) and ts_raw.strip():
                try:
                    timestamps.append(datetime.fromisoformat(ts_raw.replace("Z", "+00:00")))
                except ValueError:
                    pass

        # Compute centroid (FRP-weighted if total_frp > 0, else simple arithmetic mean)
        if total_frp > 0:
            c_lat = weighted_lat_sum / total_frp
            c_lon = weighted_lon_sum / total_frp
        else:
            c_lat = simple_lat_sum / count
            c_lon = simple_lon_sum / count

        c_lat = round(c_lat, 5)
        c_lon = round(c_lon, 5)

        if timestamps:
            first_dt = min(timestamps)
            last_dt = max(timestamps)
            first_seen = first_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            last_seen = last_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            first_seen = ""
            last_seen = ""

        clusters.append(
            {
                "clusterId": cid,
                "centroid": {"lat": c_lat, "lon": c_lon},
                "lat": c_lat,
                "lon": c_lon,
                "count": count,
                "totalFrp": round(total_frp, 2),
                "maxFrp": round(max_frp, 2),
                "firstSeen": first_seen,
                "lastSeen": last_seen,
                "firstSeenUtc": first_seen,
                "lastSeenUtc": last_seen,
            }
        )

    return clusters
