"""Geo utility functions for the DownWind impact engine.

All functions use decimal degrees (DD) for angles and kilometres for
distances.  No external dependencies — stdlib only.

Conventions:
  - Bearings / directions are clockwise from True North, 0..360 (exclusive 360).
  - ``wind_from`` is the meteorological convention: the compass direction
    *from which* the wind is blowing (e.g. 270° = wind blowing from West).
  - ``smoke_bearing`` is the direction *towards which* smoke travels, i.e.
    (wind_from + 180) % 360.
  - ``circular_mean_deg`` handles the wrap-around at 0/360 via unit-vector
    decomposition (sin/cos), so mean(350, 10) → 0°, not 180°.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EARTH_RADIUS_KM: float = 6371.0  # Mean radius, IAU 2012


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in kilometres (>= 0).  Returns 0.0 for identical points.

    Reference:
        Haversine formula — Sinnott, R.W., "Virtues of the Haversine",
        Sky and Telescope, vol.68, no.2, 1984, p.159.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    # clamp to [0, 1] to guard against floating-point rounding outside domain
    c = 2 * math.asin(math.sqrt(max(0.0, min(1.0, a))))
    return _EARTH_RADIUS_KM * c


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial (forward) bearing from point 1 to point 2, in degrees [0, 360).

    For antipodal or coincident points the bearing is undefined; this function
    returns 0.0 as a safe default (callers should check distance first).

    Args:
        lat1: Latitude of origin in decimal degrees.
        lon1: Longitude of origin in decimal degrees.
        lat2: Latitude of destination in decimal degrees.
        lon2: Longitude of destination in decimal degrees.

    Returns:
        Bearing in degrees, clockwise from True North, range [0, 360).

    Reference:
        Movable Type Scripts — "Calculate distance, bearing and more…"
        https://www.movable-type.co.uk/scripts/latlong.html
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)

    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)

    theta = math.degrees(math.atan2(x, y))
    return theta % 360.0


def smallest_angle_diff_deg(a: float, b: float) -> float:
    """Smallest unsigned angular difference between two bearings, [0, 180].

    Args:
        a: First bearing in degrees (any real number, wraps automatically).
        b: Second bearing in degrees (any real number, wraps automatically).

    Returns:
        Angular difference in degrees, always in [0, 180].

    Example:
        smallest_angle_diff_deg(10, 350) == 20.0
        smallest_angle_diff_deg(90, 270) == 180.0
    """
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def circular_mean_deg(angles: Sequence[float]) -> float:
    """Circular (directional) mean of a sequence of angles in degrees.

    Uses unit-vector decomposition so that wrap-around is handled correctly:
    mean([350, 10]) → 0.0, not 180.0.

    Args:
        angles: Non-empty sequence of angles in degrees (any real numbers).

    Returns:
        Circular mean in degrees, range [0, 360).

    Raises:
        ValueError: If ``angles`` is empty.

    Reference:
        Fisher, N.I., *Statistical Analysis of Circular Data*,
        Cambridge University Press, 1993, §2.2.
    """
    if len(angles) == 0:
        raise ValueError("circular_mean_deg requires at least one angle.")

    sin_sum = sum(math.sin(math.radians(a)) for a in angles)
    cos_sum = sum(math.cos(math.radians(a)) for a in angles)
    mean_rad = math.atan2(sin_sum, cos_sum)
    return math.degrees(mean_rad) % 360.0


def smoke_bearing_from_wind_from(wind_from_deg: float) -> float:
    """Convert meteorological wind-from direction to smoke travel bearing.

    Wind *from* the West (270°) pushes smoke *towards* the East (90°).
    Formula: ``(wind_from_deg + 180) % 360``.

    Args:
        wind_from_deg: Meteorological wind-from direction in degrees
            (any real number, wraps automatically).

    Returns:
        Smoke travel bearing in degrees, range [0, 360).

    Reference:
        Architecture spec — docs/architecture.md §6, Step 2:
        ``smoke_bearing = (dir_from + 180) % 360``
    """
    return (wind_from_deg + 180.0) % 360.0
