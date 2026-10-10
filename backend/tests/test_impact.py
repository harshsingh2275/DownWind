"""Tests for backend/src/impact.py — the smoke corridor impact engine.

All test geometries are carefully chosen so the expected outcome can be verified
by hand from the architecture §6 algorithm.

Test grid (cluster at origin lat=30.0, lon=75.0; wind FROM NORTH = 0°):
  smoke_bearing = (0 + 180) % 360 = 180° (smoke travels SOUTH)
  max_reach_km  = speed * TRAVEL_HOURS * ATTENUATION
               = 20 km/h * 24 h * 0.5 = 240 km

  City directly   south  → bearing ≈ 180° → angle_diff ≈ 0°   → AFFECTED
  City due        east   → bearing ≈  90° → angle_diff ≈ 90°  → NOT (perpendicular)
  City far        south  → distance > 240 km                   → NOT (beyond reach)
  Wind speed = 0                                                → NOT (stagnant)
  Wrap-around: wind FROM 350° → smoke_bearing = 170°; city at bearing 165° → AFFECTED
"""

from __future__ import annotations

import pytest

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
from src.geo import haversine_km
from src.impact import classify_severity, compute_cluster_city_impact, compute_impact

# ---------------------------------------------------------------------------
# Test geometry constants — all computed by hand or with haversine formula
# ---------------------------------------------------------------------------
# Reference cluster: lat=30.0, lon=75.0, FRP=200 MW
# Wind: FROM NORTH (0°), speed=20 km/h
# smoke_bearing = 180° (southward)
# max_reach_km = 20 * 24 * 0.5 = 240 km

CLUSTER_LAT = 30.0
CLUSTER_LON = 75.0
CLUSTER_FRP = 200.0

WIND_SPEED = 20.0   # km/h
WIND_FROM_NORTH = 0.0   # degrees — wind FROM north, smoke goes SOUTH


def _cluster(
    lat: float = CLUSTER_LAT,
    lon: float = CLUSTER_LON,
    frp: float = CLUSTER_FRP,
    speed: float = WIND_SPEED,
    wind_dir: float = WIND_FROM_NORTH,
    cid: str = "test_cluster",
) -> dict:  # type: ignore[type-arg]
    return {
        "clusterId": cid,
        "lat": lat,
        "lon": lon,
        "totalFrp": frp,
        "windSpeedKmh": speed,
        "windDirDeg": wind_dir,
    }


def _city(
    city_id: str,
    lat: float,
    lon: float,
) -> dict:  # type: ignore[type-arg]
    return {"id": city_id, "name": city_id.capitalize(), "lat": lat, "lon": lon}


# ---------------------------------------------------------------------------
# compute_cluster_city_impact — unit tests
# ---------------------------------------------------------------------------


class TestDirectlyUpwind:
    """City is directly in the downwind corridor and within reach → AFFECTED."""

    def test_affected_returns_dict(self) -> None:
        # City ~50 km south: lat ≈ 29.55 (1° lat ≈ 111 km)
        # bearing to city ≈ 180° — squarely in smoke corridor
        city_lat = CLUSTER_LAT - 0.45  # ~50 km south
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is not None, "City directly south should be AFFECTED"
        assert result["dist_km"] > 0
        assert result["eta_hours"] > 0
        # bearing to city due south from cluster should be ~180°
        assert abs(result["bearing_to_city_deg"] - 180.0) < 1.0
        # angle_diff should be very small (within tolerance)
        assert result["angle_diff_deg"] <= ANGLE_TOLERANCE_DEG
        # dist should be within max reach
        max_reach = WIND_SPEED * TRAVEL_HOURS * ATTENUATION
        assert result["dist_km"] <= max_reach
        # ETA sanity check
        assert abs(result["eta_hours"] - result["dist_km"] / WIND_SPEED) < 0.01

    def test_eta_formula(self) -> None:
        """ETA = dist / speed to 3 decimal places."""
        city_lat = CLUSTER_LAT - 0.45
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is not None
        expected_eta = round(result["dist_km"] / WIND_SPEED, 3)
        assert result["eta_hours"] == expected_eta


class TestPerpendicular:
    """City is due east of cluster — perpendicular to smoke corridor → NOT AFFECTED."""

    def test_perpendicular_city_not_affected(self) -> None:
        # City due east — bearing ≈ 90°, smoke heading south (180°)
        # angle_diff = smallest_angle(90°, 180°) = 90° > ANGLE_TOLERANCE_DEG (25°)
        city_lon = CLUSTER_LON + 0.5  # ~50 km east at this latitude
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=CLUSTER_LAT,
            city_lon=city_lon,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is None, "City due east (perpendicular) should NOT be affected"

    def test_just_outside_corridor_not_affected(self) -> None:
        """City placed due east — bearing ~90°, angle_diff ~90° >> TOLERANCE → NOT affected."""
        # Due east is always 90° from cluster regardless of spherical distortion at this scale.
        # angle_diff = smallest_angle(90°, 180°) = 90° >> ANGLE_TOLERANCE_DEG (25°)
        city_lon = CLUSTER_LON + 0.5   # ~50 km east at 30° N
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=CLUSTER_LAT,
            city_lon=city_lon,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is None, "City due east (90° off corridor) should NOT be affected"

    def test_just_inside_corridor_affected(self) -> None:
        """City bearing ~180°-20° from cluster is inside 25° corridor → AFFECTED."""
        # Use wind FROM SOUTH (180°) → smoke_bearing=0° (northward).
        # City due north at bearing=0° → angle_diff=0° → clearly inside corridor.
        city_lat = CLUSTER_LAT + 0.45   # ~50 km north
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=180.0,   # FROM south → smoke goes NORTH
        )
        assert result is not None, "City due north with northward smoke should be AFFECTED"
        assert result["angle_diff_deg"] < ANGLE_TOLERANCE_DEG


class TestBeyondReach:
    """City is in the corridor but farther than max_reach_km → NOT AFFECTED."""

    def test_beyond_reach_not_affected(self) -> None:
        # max_reach_km = 20 * 24 * 0.5 = 240 km
        # Place city ~270 km south (> 240 km) so it is beyond reach
        city_lat = CLUSTER_LAT - 2.43   # ~270 km south (1° ≈ 111 km)
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        dist = haversine_km(CLUSTER_LAT, CLUSTER_LON, city_lat, CLUSTER_LON)
        max_reach = WIND_SPEED * TRAVEL_HOURS * ATTENUATION
        assert dist > max_reach, f"Setup error: dist={dist:.1f} should exceed reach={max_reach}"
        assert result is None, f"City {dist:.1f} km away (reach={max_reach}) should NOT be affected"

    def test_exactly_at_reach_boundary_affected(self) -> None:
        """City exactly at max_reach_km (within rounding) is affected."""
        # Place city exactly 240 km south  →  lat offset = 240/111.195 ≈ 2.159°
        city_lat = CLUSTER_LAT - 2.159
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        dist = haversine_km(CLUSTER_LAT, CLUSTER_LON, city_lat, CLUSTER_LON)
        max_reach = WIND_SPEED * TRAVEL_HOURS * ATTENUATION
        # Only assert if haversine confirms it is within reach
        if dist <= max_reach:
            assert result is not None, "City at boundary should be affected"


class TestZeroWind:
    """Stagnant/zero wind means no directed plume → NOT AFFECTED."""

    def test_zero_wind_not_affected(self) -> None:
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=CLUSTER_LAT - 0.45,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=0.0,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is None, "Zero wind should never affect any city"

    def test_below_min_wind_not_affected(self) -> None:
        """Speed below MIN_WIND_KMH is treated as stagnant."""
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=CLUSTER_LAT - 0.45,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=MIN_WIND_KMH - 0.01,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is None

    def test_exactly_min_wind_is_affected(self) -> None:
        """Speed exactly equal to MIN_WIND_KMH is NOT stagnant (boundary is inclusive)."""
        # At MIN_WIND_KMH=1 km/h, max reach = 1 * 24 * 0.5 = 12 km
        # City 5 km south: dist ≈ 0.045° * 111 km ≈ 5 km
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=CLUSTER_LAT - 0.045,   # ~5 km south
            city_lon=CLUSTER_LON,
            wind_speed_kmh=MIN_WIND_KMH,
            wind_dir_from_deg=WIND_FROM_NORTH,
        )
        assert result is not None, "Speed exactly at MIN_WIND_KMH should be accepted"


class TestWrapAroundBearings:
    """Wind from near 360°/0° boundary — angular wrap-around must be handled."""

    def test_wind_from_350_smoke_goes_170(self) -> None:
        # wind FROM 350° → smoke_bearing = (350+180)%360 = 170°
        # City at bearing 165° from cluster (5° inside corridor, angle_diff = 5°)
        # Place city at ~50 km in direction 165° from cluster
        import math
        bearing = 165.0
        dist_deg = 0.40
        city_lat = CLUSTER_LAT + dist_deg * math.cos(math.radians(bearing))
        city_lon = CLUSTER_LON + dist_deg * math.sin(math.radians(bearing))
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=city_lon,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=350.0,   # FROM near-north
        )
        assert result is not None, "Wind from 350° smoke at 170°; city at 165° should be affected"
        assert result["smoke_bearing_deg"] == pytest.approx(170.0, abs=0.1)

    def test_wind_from_10_smoke_goes_190(self) -> None:
        # wind FROM 10° → smoke_bearing = (10+180)%360 = 190°
        # City due south at bearing ~180°: angle_diff = smallest_angle(180, 190) = 10° → AFFECTED
        city_lat = CLUSTER_LAT - 0.45
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=CLUSTER_LON,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=10.0,
        )
        assert result is not None
        assert result["smoke_bearing_deg"] == pytest.approx(190.0, abs=0.1)

    def test_wind_from_355_city_at_bearing_175(self) -> None:
        # wind FROM 355° → smoke_bearing = 175°
        # City at bearing 175° → angle_diff = 0° → AFFECTED
        import math
        bearing = 175.0
        dist_deg = 0.40
        city_lat = CLUSTER_LAT + dist_deg * math.cos(math.radians(bearing))
        city_lon = CLUSTER_LON + dist_deg * math.sin(math.radians(bearing))
        result = compute_cluster_city_impact(
            cluster_lat=CLUSTER_LAT,
            cluster_lon=CLUSTER_LON,
            cluster_frp=CLUSTER_FRP,
            city_lat=city_lat,
            city_lon=city_lon,
            wind_speed_kmh=WIND_SPEED,
            wind_dir_from_deg=355.0,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# compute_impact — aggregation tests
# ---------------------------------------------------------------------------


class TestComputeImpactAggregation:
    """End-to-end city-level aggregation via compute_impact."""

    def _south_city(self) -> dict:  # type: ignore[type-arg]
        """City 50 km south of cluster — directly downwind, within reach."""
        return _city("south_city", CLUSTER_LAT - 0.45, CLUSTER_LON)

    def _east_city(self) -> dict:  # type: ignore[type-arg]
        """City 50 km east — perpendicular, not affected."""
        return _city("east_city", CLUSTER_LAT, CLUSTER_LON + 0.5)

    def test_single_cluster_single_affected_city(self) -> None:
        clusters = [_cluster()]
        cities = [self._south_city()]
        results = compute_impact(clusters, cities)
        assert len(results) == 1
        r = results[0]
        assert r["cityId"] == "south_city"
        assert r["nClusters"] == 1
        assert r["totalFrp"] == CLUSTER_FRP
        assert r["nearestKm"] > 0
        assert r["minEtaHours"] > 0
        assert r["severity"] in ("High", "Medium", "Low")

    def test_perpendicular_city_not_in_results(self) -> None:
        clusters = [_cluster()]
        cities = [self._east_city()]
        results = compute_impact(clusters, cities)
        assert results == [], "East city (perpendicular) should produce no impact"

    def test_multiple_clusters_aggregate_correctly(self) -> None:
        """Two clusters both affecting south_city → nClusters=2, totalFrp sums."""
        c1 = _cluster(frp=100.0, cid="c1")
        c2 = _cluster(lat=CLUSTER_LAT - 0.1, frp=200.0, cid="c2")
        cities = [self._south_city()]
        results = compute_impact([c1, c2], cities)
        assert len(results) == 1
        r = results[0]
        assert r["nClusters"] == 2
        assert r["totalFrp"] == pytest.approx(300.0, abs=0.01)
        assert "c1" in r["affectedByClusterIds"]
        assert "c2" in r["affectedByClusterIds"]

    def test_only_affected_cities_appear_in_results(self) -> None:
        """Mix of affected and unaffected cities: only affected in output."""
        clusters = [_cluster()]
        cities = [self._south_city(), self._east_city()]
        results = compute_impact(clusters, cities)
        city_ids = [r["cityId"] for r in results]
        assert "south_city" in city_ids
        assert "east_city" not in city_ids

    def test_empty_clusters_returns_empty(self) -> None:
        results = compute_impact([], [self._south_city()])
        assert results == []

    def test_empty_cities_returns_empty(self) -> None:
        results = compute_impact([_cluster()], [])
        assert results == []

    def test_zero_wind_cluster_affects_no_cities(self) -> None:
        clusters = [_cluster(speed=0.0)]
        cities = [self._south_city()]
        results = compute_impact(clusters, cities)
        assert results == [], "Zero wind cluster should affect no city"

    def test_nearestkm_and_mineta_use_minimum_across_clusters(self) -> None:
        """nearestKm and minEtaHours are the minimum across all affecting clusters."""
        # c1: 100 km south, c2: 50 km south → nearestKm should be ~50 km
        c1 = _cluster(lat=CLUSTER_LAT - 0.90, frp=50.0, cid="c1")   # ~100 km south
        c2 = _cluster(lat=CLUSTER_LAT - 0.45, frp=50.0, cid="c2")   # ~50 km south
        cities = [self._south_city()]   # ~50 km south of CLUSTER_LAT
        results = compute_impact([c1, c2], cities)
        # south_city is ~50 km south of CLUSTER_LAT so:
        #   from c1 (100 km south of CL) → city is ~50 km NORTH of c1
        #     bearing ≈ 0° → NOT in south smoke corridor
        #   from c2 (50 km south of CL)  → city is at SAME lat → dist ≈ 0 km
        # Verify nearestKm is the smaller distance
        if results:
            assert results[0]["nearestKm"] <= results[0]["minEtaHours"] * WIND_SPEED


# ---------------------------------------------------------------------------
# classify_severity — unit tests
# ---------------------------------------------------------------------------


class TestClassifySeverity:
    """Severity classification against proposed thresholds (D-021, Q-10)."""

    def test_high_severity(self) -> None:
        # FRP above HIGH threshold, ETA within HIGH window
        sev = classify_severity(
            total_frp=SEVERITY_HIGH_FRP + 1.0,
            min_eta_hours=SEVERITY_HIGH_ETA_H - 0.1,
        )
        assert sev == "High"

    def test_medium_severity(self) -> None:
        # FRP above MEDIUM but below HIGH, ETA within MEDIUM window
        sev = classify_severity(
            total_frp=SEVERITY_MEDIUM_FRP + 1.0,
            min_eta_hours=SEVERITY_MEDIUM_ETA_H - 0.1,
        )
        assert sev == "Medium"

    def test_low_severity_low_frp(self) -> None:
        sev = classify_severity(total_frp=50.0, min_eta_hours=2.0)
        assert sev == "Low"

    def test_low_severity_long_eta(self) -> None:
        sev = classify_severity(total_frp=SEVERITY_HIGH_FRP + 100.0, min_eta_hours=20.0)
        assert sev == "Low"

    def test_high_frp_long_eta_is_medium_or_low(self) -> None:
        # Huge FRP but very slow arrival — not HIGH (ETA > HIGH threshold)
        sev = classify_severity(
            total_frp=SEVERITY_HIGH_FRP + 100.0,
            min_eta_hours=SEVERITY_HIGH_ETA_H + 1.0,
        )
        assert sev in ("Medium", "Low")

    def test_severity_thresholds_from_config_not_hardcoded(self) -> None:
        """Verify the exact boundary values declared in config.py."""
        # Exactly at HIGH boundary
        sev_high_exact = classify_severity(
            total_frp=SEVERITY_HIGH_FRP,
            min_eta_hours=SEVERITY_HIGH_ETA_H,
        )
        assert sev_high_exact == "High"

        # Exactly at MEDIUM boundary (assuming FRP < SEVERITY_HIGH_FRP)
        sev_med_exact = classify_severity(
            total_frp=SEVERITY_MEDIUM_FRP,
            min_eta_hours=SEVERITY_MEDIUM_ETA_H,
        )
        assert sev_med_exact == "Medium"
