"""Central configuration module for DownWind.

Contains every tunable heuristic and threshold defined in docs/architecture.md
section 6. Magic numbers must never be hardcoded elsewhere in the codebase.
"""

from __future__ import annotations

# ==============================================================================
# Architecture.md Section 6: Tunable Algorithm Parameters (Heuristics)
# ==============================================================================

# Grid cell dimension (in degrees) for spatial fire clustering (~5.5 km at 30° N)
CLUSTER_GRID_DEG: float = 0.05

# Minimum detection confidence threshold ('low' confidence detections are dropped)
MIN_CONFIDENCE: str = "nominal"

# Angular tolerance (half-width in degrees) of the downwind smoke dispersion corridor
ANGLE_TOLERANCE_DEG: float = 25.0

# Maximum forward projection time horizon (in hours) for smoke travel
TRAVEL_HOURS: float = 24.0

# Atmospheric and dispersion attenuation factor reducing effective smoke reach
ATTENUATION: float = 0.5

# Minimum effective wind speed in km/h below which plume is considered stagnant
# Also serves as guard against divide-by-zero during ETA computation
MIN_WIND_KMH: float = 1.0

# Cooldown window (in hours) before repeating an alert for the same city
ALERT_COOLDOWN_HOURS: float = 12.0

# ==============================================================================
# External API and Operational Boundaries
# ==============================================================================

# NASA FIRMS Area API maximum query day range supported per request (T-004 verified)
FIRMS_MAX_DAY_RANGE: int = 5

# Open-Meteo multi-location maximum coordinates supported per GET call (T-004 verified)
OPEN_METEO_MAX_LOCATIONS: int = 1000

# Coarse meteorological sampling grid step in degrees for regional wind forecast
WIND_GRID_STEP_DEG: float = 0.5

# Default hourly forecast window for wind evaluation
DEFAULT_WIND_WINDOW_HOURS: int = 24

# ==============================================================================
# Severity Thresholds (Heuristic — UNVALIDATED; pending owner confirmation Q-10)
# ==============================================================================
# Severity is a two-axis classification: fire intensity (totalFrp, MW) and
# proximity/urgency (minEtaHours, hours).
#
# Reasoning:
#   HIGH:   FRP > 500 MW is a large, highly active fire cluster; ETA < 6 h means
#           smoke could reach the city within a single morning/evening window.
#           Punjab stubble fires routinely exceed 200 MW; 500 MW is the upper tier.
#   MEDIUM: FRP > 150 MW is a moderate cluster (several simultaneous burns);
#           ETA < 12 h covers same-day impact across most city distances.
#   LOW:    Anything detected within the reach corridor but below MEDIUM thresholds.
#
# ⚠ These values are proposals — record as D-021.  Owner must confirm or adjust
#   before production use (Q-10).  UI should label all severity as "Indicative".

SEVERITY_HIGH_FRP: float = 500.0      # MW — minimum totalFrp for HIGH
SEVERITY_HIGH_ETA_H: float = 6.0      # hours — maximum minEtaHours for HIGH
SEVERITY_MEDIUM_FRP: float = 150.0    # MW — minimum totalFrp for MEDIUM
SEVERITY_MEDIUM_ETA_H: float = 12.0   # hours — maximum minEtaHours for MEDIUM
