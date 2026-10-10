"""Pure-Python GeoJSON region filtering and polygon utilities."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence


def point_in_ring(lon: float, lat: float, ring: Sequence[Sequence[float]]) -> bool:
    """Determine if a point (lon, lat) is inside a linear polygon ring using Ray-Casting.

    Ring coordinates are ordered as [lon, lat].
    """
    inside = False
    n = len(ring)
    if n < 3:
        return False

    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]

        # Ray casting test
        intersect = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        )
        if intersect:
            inside = not inside
        j = i

    return inside


def point_in_polygon(lon: float, lat: float, coordinates: list[list[list[float]]]) -> bool:
    """Test point in polygon with exterior ring and optional interior hole rings."""
    if not coordinates:
        return False

    # First ring is exterior boundary
    exterior = coordinates[0]
    if not point_in_ring(lon, lat, exterior):
        return False

    # Subsequent rings are interior holes
    for hole in coordinates[1:]:
        if point_in_ring(lon, lat, hole):
            return False

    return True


def point_in_multipolygon(
    lon: float, lat: float, coordinates: list[list[list[list[float]]]]
) -> bool:
    """Test point in any constituent polygon of a MultiPolygon."""
    for poly_coords in coordinates:
        if point_in_polygon(lon, lat, poly_coords):
            return True
    return False


def is_point_in_geometry(lon: float, lat: float, geometry: dict[str, Any]) -> bool:
    """Check if point is inside a GeoJSON geometry."""
    geom_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates")

    if geom_type == "Polygon" and isinstance(coordinates, list):
        return point_in_polygon(lon, lat, coordinates)
    if geom_type == "MultiPolygon" and isinstance(coordinates, list):
        return point_in_multipolygon(lon, lat, coordinates)
    return False


def is_point_in_geojson(lat: float, lon: float, geojson_data: dict[str, Any]) -> bool:
    """Check if (lat, lon) coordinates fall inside a GeoJSON object."""
    obj_type = geojson_data.get("type", "")

    if obj_type == "FeatureCollection":
        features = geojson_data.get("features", [])
        for feature in features:
            geom = feature.get("geometry", {})
            if is_point_in_geometry(lon, lat, geom):
                return True
        return False

    if obj_type == "Feature":
        geom = geojson_data.get("geometry", {})
        return is_point_in_geometry(lon, lat, geom)

    if obj_type in ("Polygon", "MultiPolygon"):
        return is_point_in_geometry(lon, lat, geojson_data)

    return False


def perpendicular_distance(
    point: Sequence[float], line_start: Sequence[float], line_end: Sequence[float]
) -> float:
    """Perpendicular distance from a point to a line segment."""
    x0, y0 = point[0], point[1]
    x1, y1 = line_start[0], line_start[1]
    x2, y2 = line_end[0], line_end[1]

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(x0 - x1, y0 - y1)

    numerator = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1)
    denominator = math.hypot(dx, dy)
    return numerator / denominator


def ramer_douglas_peucker(
    points: Sequence[Sequence[float]], tolerance: float
) -> list[list[float]]:
    """Simplify a list of points using the Ramer-Douglas-Peucker algorithm."""
    if len(points) <= 2:
        return [list(p) for p in points]

    dmax = 0.0
    index = 0
    end = len(points) - 1

    for i in range(1, end):
        d = perpendicular_distance(points[i], points[0], points[end])
        if d > dmax:
            index = i
            dmax = d

    if dmax > tolerance:
        rec_results1 = ramer_douglas_peucker(points[: index + 1], tolerance)
        rec_results2 = ramer_douglas_peucker(points[index:], tolerance)
        return rec_results1[:-1] + rec_results2
    else:
        return [list(points[0]), list(points[end])]


def simplify_ring(ring: Sequence[Sequence[float]], tolerance: float) -> list[list[float]]:
    """Simplify a closed polygon ring while ensuring it remains closed."""
    if len(ring) <= 4:
        return [list(p) for p in ring]

    # RDP on the open sequence, then re-close
    is_closed = ring[0] == ring[-1]
    pts = ring[:-1] if is_closed else ring

    simplified = ramer_douglas_peucker(pts, tolerance)
    if is_closed and simplified[0] != simplified[-1]:
        simplified.append(simplified[0])

    if len(simplified) < 4:
        return [list(p) for p in ring]

    return simplified


def simplify_geojson_geometry(geometry: dict[str, Any], tolerance: float) -> dict[str, Any]:
    """Simplify all rings in a Polygon or MultiPolygon geometry."""
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        new_coords = [simplify_ring(ring, tolerance) for ring in coords]
        return {"type": "Polygon", "coordinates": new_coords}

    if geom_type == "MultiPolygon":
        new_coords_multi = [
            [simplify_ring(ring, tolerance) for ring in poly] for poly in coords
        ]
        return {"type": "MultiPolygon", "coordinates": new_coords_multi}

    return geometry


def load_region_boundary(filepath: Path | str) -> dict[str, Any]:
    """Load region boundary GeoJSON from file."""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]
