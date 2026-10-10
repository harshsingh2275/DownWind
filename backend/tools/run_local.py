"""Local end-to-end execution of DownWind pipeline (T-027).

Fetches satellite fire detections from NASA FIRMS Area API, filters them
within Punjab & Haryana state boundaries, clusters thermal anomalies,
queries regional wind fields from Open-Meteo, computes smoke corridor impacts
on receptor cities, and prints a formatted summary.

Security:
  - The NASA FIRMS MAP_KEY is read strictly from an environment variable (FIRMS_MAP_KEY).
  - The key is NEVER printed, logged, or written to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clustering import cluster_detections
from src.config import (
    CLUSTER_GRID_DEG,
    DEFAULT_WIND_WINDOW_HOURS,
    WIND_GRID_STEP_DEG,
)
from src.firms import fetch_firms_csv, parse_firms_csv
from src.impact import compute_impact
from src.region import is_point_in_geojson, load_region_boundary
from src.wind import (
    assign_wind_to_cluster,
    build_wind_grid,
    fetch_wind_data,
    parse_wind_forecast,
)

_BACKEND_DIR: Path = Path(__file__).resolve().parent.parent

# Geographic bounds for Punjab & Haryana regional query
DEFAULT_AREA_BBOX: str = "73.8,27.6,77.6,32.5"  # west,south,east,north
DEFAULT_NRT_SOURCE: str = "VIIRS_NOAA20_NRT"
DEFAULT_ARCHIVE_SOURCE: str = "VIIRS_NOAA20_SP"
DEFAULT_FALLBACK_ARCHIVE_DATE: str = "2024-11-01"  # Peak stubble season verified in T-004


def print_env_var_instructions() -> None:
    """Print clear instructions on how to set FIRMS_MAP_KEY for the current session."""
    msg = """
================================================================================
[ERROR] NASA FIRMS MAP_KEY is not set in the environment!
================================================================================

To run DownWind locally, set the FIRMS_MAP_KEY environment variable in your terminal
session (valid for this session only, never saved to disk or committed):

  PowerShell (Windows):
    $env:FIRMS_MAP_KEY="<your_32_char_nasa_firms_key>"

  Command Prompt (cmd.exe):
    set FIRMS_MAP_KEY=<your_32_char_nasa_firms_key>

  Bash / Git Bash / macOS / Linux:
    export FIRMS_MAP_KEY="<your_32_char_nasa_firms_key>"

Important Security & Usage Guidelines:
  - Never commit or hardcode your key into any file or git repository.
  - Never paste your key into chat messages or issues.
  - Get a free key anytime at: https://firms.modaps.eosdis.nasa.gov/api/map_key/
================================================================================
"""
    print(msg, file=sys.stderr)


def get_map_key(allow_empty: bool = False) -> str | None:
    """Retrieve NASA FIRMS MAP_KEY from environment variables."""
    key = os.environ.get("FIRMS_MAP_KEY") or os.environ.get("MAP_KEY")
    if key:
        clean = key.strip()
        if clean:
            return clean
    if not allow_empty:
        print_env_var_instructions()
    return None


def run_pipeline(
    map_key: str | None = None,
    date: str | None = None,
    source: str | None = None,
    area: str = DEFAULT_AREA_BBOX,
    day_range: int = 1,
    fallback_archive_date: str = DEFAULT_FALLBACK_ARCHIVE_DATE,
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    """Execute the full DownWind pipeline end-to-end and print readable summary.

    Returns:
        Dictionary with execution metrics and results.
    """
    print("=" * 80)
    print("           DownWind - Stubble Smoke Tracking Engine (Local Run)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Security check on key
    if fixture_path is None:
        if not map_key:
            map_key = get_map_key()
            if not map_key:
                return {"success": False, "error": "MISSING_MAP_KEY"}
        print("FIRMS Credential: [CONFIGURED - Hidden for security]")
    else:
        print(f"FIRMS Source: [FIXTURE FILE: {fixture_path}]")

    data_dir = _BACKEND_DIR / "data"
    region_path = data_dir / "region.geojson"
    cities_path = data_dir / "cities.json"

    if not region_path.exists():
        print(f"[ERROR] Region boundary file not found at {region_path}", file=sys.stderr)
        return {"success": False, "error": "MISSING_REGION_FILE"}

    if not cities_path.exists():
        print(f"[ERROR] Cities data file not found at {cities_path}", file=sys.stderr)
        return {"success": False, "error": "MISSING_CITIES_FILE"}

    # --------------------------------------------------------------------------
    # Stage 1: Fetch NASA FIRMS Detections
    # --------------------------------------------------------------------------
    active_source = source or (DEFAULT_ARCHIVE_SOURCE if date else DEFAULT_NRT_SOURCE)
    active_date = date
    used_fallback_archive = False

    print("\n--> [Stage 1/5] Fetching NASA FIRMS Satellite Fire Detections...")
    if fixture_path:
        with open(fixture_path, "r", encoding="utf-8") as f:
            raw_csv = f.read()
        mode_label = f"Fixture ({Path(fixture_path).name})"
    else:
        assert map_key is not None
        print(f"    Target Area: {area}")
        print(f"    Sensor Source: {active_source}")
        if active_date:
            print(f"    Date: {active_date} (Day Range: {day_range})")
        else:
            print(f"    Mode: Near Real-Time (Day Range: {day_range})")

        try:
            raw_csv = fetch_firms_csv(
                map_key=map_key,
                source=active_source,
                area=area,
                day_range=day_range,
                date=active_date,
            )
        except Exception as exc:
            print(f"[ERROR] Failed to fetch FIRMS data: {exc}", file=sys.stderr)
            return {"success": False, "error": f"FIRMS_FETCH_ERROR: {exc}"}
        mode_label = f"{active_source} ({active_date or 'NRT'})"

    # Parse and filter confidence
    detections = parse_firms_csv(raw_csv)
    print(f"    Raw observations parsed (confidence >= nominal): {len(detections)}")

    # --------------------------------------------------------------------------
    # Stage 2: State Boundary Region Filter
    # --------------------------------------------------------------------------
    print("\n--> [Stage 2/5] Filtering detections by Punjab & Haryana boundaries...")
    region_data = load_region_boundary(region_path)
    in_region = [d for d in detections if is_point_in_geojson(d["lat"], d["lon"], region_data)]
    print(f"    Detections inside region (IN-PB / IN-HR): {len(in_region)}")

    # Fallback to historical archive if no fires exist in NRT
    if len(in_region) == 0 and not active_date and not fixture_path:
        print("\n    [NOTICE] No active fires detected in Near Real-Time (NRT) today.")
        print(
            f"    Switching to historical stubble burning archive date: {fallback_archive_date}"
        )
        print(
            f"    Archive source: '{DEFAULT_ARCHIVE_SOURCE}' "
            "(Standard Processing, verified in T-004)..."
        )
        try:
            assert map_key is not None
            raw_csv = fetch_firms_csv(
                map_key=map_key,
                source=DEFAULT_ARCHIVE_SOURCE,
                area=area,
                day_range=day_range,
                date=fallback_archive_date,
            )
            detections = parse_firms_csv(raw_csv)
            in_region = [
                d for d in detections if is_point_in_geojson(d["lat"], d["lon"], region_data)
            ]
            active_source = DEFAULT_ARCHIVE_SOURCE
            active_date = fallback_archive_date
            used_fallback_archive = True
            mode_label = f"{DEFAULT_ARCHIVE_SOURCE} ({fallback_archive_date})"
            print(f"    Archive detections parsed: {len(detections)}")
            print(f"    Archive detections inside region: {len(in_region)}")
        except Exception as exc:
            print(f"[WARNING] Archive fallback fetch encountered an issue: {exc}", file=sys.stderr)

    # --------------------------------------------------------------------------
    # Stage 3: Spatial Clustering
    # --------------------------------------------------------------------------
    print("\n--> [Stage 3/5] Clustering fire detections (Grid: 0.05 deg ~ 5.5 km)...")
    clusters = cluster_detections(in_region, grid_deg=CLUSTER_GRID_DEG)
    total_frp = sum(float(c.get("totalFrp", 0.0)) for c in clusters)
    max_frp = max((float(c.get("maxFrp", 0.0)) for c in clusters), default=0.0)
    print(f"    Clusters formed: {len(clusters)}")
    print(f"    Total Fire Radiative Power (FRP): {total_frp:.1f} MW")
    print(f"    Peak Cluster FRP: {max_frp:.1f} MW")

    # --------------------------------------------------------------------------
    # Stage 4: Regional Wind Field (Open-Meteo)
    # --------------------------------------------------------------------------
    print("\n--> [Stage 4/5] Fetching regional meteorological wind field (Open-Meteo)...")
    grid_points = build_wind_grid(
        min_lat=27.5,
        max_lat=32.5,
        min_lon=73.5,
        max_lon=77.5,
        step_deg=WIND_GRID_STEP_DEG,
    )
    print(f"    Coarse sampling grid: {len(grid_points)} coordinates across region")

    try:
        # Use archive weather API if historical archive date is active
        wind_date = active_date if (active_date and used_fallback_archive) else None
        if wind_date:
            print(f"    Querying Open-Meteo Historical Archive API for {wind_date}...")
        else:
            print("    Querying Open-Meteo Forecast API...")

        wind_raw = fetch_wind_data(
            grid_points=grid_points,
            date=wind_date,
            window_hours=DEFAULT_WIND_WINDOW_HOURS,
        )
        grid_wind_map = parse_wind_forecast(wind_raw, window_hours=DEFAULT_WIND_WINDOW_HOURS)
        print(f"    Wind observations parsed for {len(grid_wind_map)} grid points")

        # Assign nearest wind to each cluster
        for cluster in clusters:
            assign_wind_to_cluster(cluster, grid_wind_map)

        speeds = [w[0] for w in grid_wind_map.values()]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        print(
            f"    Regional wind speed range: {min(speeds):.1f} - {max(speeds):.1f} km/h "
            f"(Average: {avg_speed:.1f} km/h)"
        )
    except Exception as exc:
        print(f"[ERROR] Failed to fetch regional wind data: {exc}", file=sys.stderr)
        return {"success": False, "error": f"WIND_FETCH_ERROR: {exc}"}

    # --------------------------------------------------------------------------
    # Stage 5: Downwind Smoke Impact Engine
    # --------------------------------------------------------------------------
    print("\n--> [Stage 5/5] Computing smoke corridor dispersion and city impacts...")
    with open(cities_path, "r", encoding="utf-8") as f:
        cities = json.load(f)

    impacts = compute_impact(clusters, cities)
    print(f"    Receptor cities evaluated: {len(cities)}")
    print(f"    Cities with smoke plume impact: {len(impacts)}")

    # --------------------------------------------------------------------------
    # Summary Report
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("                    DOWNWIND PIPELINE EXECUTION SUMMARY")
    print(f"                    Data Mode: {mode_label}")
    print("=" * 80)

    if impacts:
        print(
            f"{'City':<14} {'State':<14} {'Severity':<10} {'Clusters':<10} "
            f"{'FRP (MW)':<12} {'Nearest (km)':<14} {'ETA (h)':<8}"
        )
        print("-" * 84)
        for imp in impacts:
            c_name = imp.get("cityName", imp.get("cityId", ""))
            # Find city state
            c_state = next((c.get("state", "") for c in cities if c.get("id") == imp["cityId"]), "")
            print(
                f"{c_name:<14} {c_state:<14} {imp['severity']:<10} {imp['nClusters']:<10} "
                f"{imp['totalFrp']:<12.1f} {imp['nearestKm']:<14.1f} {imp['minEtaHours']:<8.1f}"
            )
    else:
        print("No receptor cities currently fall inside downwind smoke dispersion corridors.")

    print("\n" + "-" * 80)
    print("Heuristic & Attribution Notes:")
    print("  * Severity ratings (High/Medium/Low) are heuristic approximations (Q-10 / D-021).")
    print("  * Active fire data: NASA FIRMS (VIIRS).")
    print("  * Meteorological wind data: Open-Meteo (CC BY 4.0).")
    print("  * Administrative boundaries: geoBoundaries (CC BY 4.0).")
    print("=" * 80 + "\n")

    return {
        "success": True,
        "mode": mode_label,
        "date": active_date,
        "source": active_source,
        "used_fallback_archive": used_fallback_archive,
        "raw_detections": len(detections),
        "in_region_detections": len(in_region),
        "clusters_count": len(clusters),
        "total_frp": total_frp,
        "max_frp": max_frp,
        "affected_cities_count": len(impacts),
        "impacts": impacts,
    }


def main() -> int:
    """CLI entry point for backend/tools/run_local.py."""
    parser = argparse.ArgumentParser(
        description="DownWind - Local End-to-End Pipeline Execution Tool"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Acquisition date (YYYY-MM-DD). If omitted, defaults to near real-time.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="NASA FIRMS source (e.g. VIIRS_NOAA20_NRT, VIIRS_NOAA20_SP, MODIS_NRT).",
    )
    parser.add_argument(
        "--area",
        type=str,
        default=DEFAULT_AREA_BBOX,
        help=f"Bounding box west,south,east,north (default: {DEFAULT_AREA_BBOX}).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Day range 1 to 5 (default: 1).",
    )
    parser.add_argument(
        "--archive-date",
        type=str,
        default=DEFAULT_FALLBACK_ARCHIVE_DATE,
        help=(
            f"Historical fallback date if no fires found "
            f"(default: {DEFAULT_FALLBACK_ARCHIVE_DATE})."
        ),
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default=None,
        help="Optional local CSV fixture path for offline demonstration/testing.",
    )

    args = parser.parse_args()

    key: str | None = None
    if not args.fixture:
        key = get_map_key()
        if not key:
            return 1

    result = run_pipeline(
        map_key=key,
        date=args.date,
        source=args.source,
        area=args.area,
        day_range=args.days,
        fallback_archive_date=args.archive_date,
        fixture_path=Path(args.fixture) if args.fixture else None,
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
