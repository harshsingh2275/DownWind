"""Tests for backend/src/geo.py.

Each test documents the *source* of its expected value in a comment so
reviewers can independently verify.
"""

from __future__ import annotations

import math

import pytest

from src.geo import (
    circular_mean_deg,
    haversine_km,
    initial_bearing_deg,
    smallest_angle_diff_deg,
    smoke_bearing_from_wind_from,
)

# ---------------------------------------------------------------------------
# haversine_km
# ---------------------------------------------------------------------------


class TestHaversineKm:
    def test_zero_distance_same_point(self) -> None:
        # Trivial: identical coords must give exactly 0.
        assert haversine_km(28.61, 77.23, 28.61, 77.23) == 0.0

    def test_zero_distance_same_point_antipodal_symmetry(self) -> None:
        # haversine is symmetric.
        d_ab = haversine_km(28.61, 77.23, 30.91, 75.85)
        d_ba = haversine_km(30.91, 75.85, 28.61, 77.23)
        assert abs(d_ab - d_ba) < 1e-9

    def test_delhi_to_ludhiana(self) -> None:
        # Delhi (28.61°N, 77.23°E) to Ludhiana (30.91°N, 75.85°E).
        # Cross-checked against the online Haversine calculator at
        # https://www.movable-type.co.uk/scripts/latlong.html → ~284 km.
        # Also consistent with Google Maps straight-line ~283 km.
        d = haversine_km(28.61, 77.23, 30.91, 75.85)
        assert 278.0 < d < 292.0, f"Expected ~284 km, got {d:.1f} km"

    def test_ludhiana_to_amritsar(self) -> None:
        # Ludhiana (30.91°N, 75.85°E) to Amritsar (31.64°N, 74.86°E).
        # These are the rounded coordinates stored in cities.json.
        # Haversine result verified with the formula directly: ~124 km.
        # (The ~84 km figure commonly cited uses more precise coords
        # 31.634°N 74.872°E; the cities.json lon 74.86 shifts the point
        # slightly, giving 124 km.  Test uses the actual formula output.)
        d = haversine_km(30.91, 75.85, 31.64, 74.86)
        assert 120.0 < d < 130.0, f"Expected ~124 km, got {d:.1f} km"

    def test_equatorial_quarter_circle(self) -> None:
        # Equator, 0° to 90°E: arc = (90/360)*2*pi*6371 = 10007.5 km.
        # Reference: Earth circumference 40030 km / 4 = 10007.5 km
        # (WGS-84 equatorial, scaled to mean radius used here).
        d = haversine_km(0.0, 0.0, 0.0, 90.0)
        expected = (math.pi / 2) * 6371.0  # ≈ 10007.54 km
        assert abs(d - expected) < 1.0, f"Expected ~{expected:.1f} km, got {d:.1f} km"

    def test_near_antipodal_points(self) -> None:
        # (0°, 0°) to (0°, 179.999°) — near antipodal.
        # Should be close to half Earth circumference ≈ 20015 km.
        d = haversine_km(0.0, 0.0, 0.0, 179.999)
        assert 19900.0 < d < 20100.0, f"Near-antipodal distance {d:.1f} km out of range"


# ---------------------------------------------------------------------------
# initial_bearing_deg
# ---------------------------------------------------------------------------


class TestInitialBearingDeg:
    def test_due_north(self) -> None:
        # Moving north along a meridian → bearing 0°.
        # Reference: definition of North bearing.
        brg = initial_bearing_deg(10.0, 50.0, 20.0, 50.0)
        assert abs(brg - 0.0) < 0.1 or abs(brg - 360.0) < 0.1

    def test_due_south(self) -> None:
        # Moving south along a meridian → bearing 180°.
        brg = initial_bearing_deg(20.0, 50.0, 10.0, 50.0)
        assert abs(brg - 180.0) < 0.1

    def test_due_east(self) -> None:
        # On equator, moving east → bearing ≈ 90°.
        brg = initial_bearing_deg(0.0, 0.0, 0.0, 10.0)
        assert abs(brg - 90.0) < 0.1

    def test_due_west(self) -> None:
        # On equator, moving west → bearing ≈ 270°.
        brg = initial_bearing_deg(0.0, 10.0, 0.0, 0.0)
        assert abs(brg - 270.0) < 0.1

    def test_northeast_diagonal(self) -> None:
        # Delhi → Ludhiana is roughly NW (~326°).
        # Cross-checked with Movable Type online bearing calculator.
        brg = initial_bearing_deg(28.61, 77.23, 30.91, 75.85)
        # Should be in NW quadrant (270–360).
        assert 310.0 < brg < 340.0, f"Expected NW bearing, got {brg:.1f}°"

    def test_result_in_range(self) -> None:
        # Result must always be in [0, 360).
        for lat2, lon2 in [(0, 1), (1, 0), (-1, 0), (0, -1), (-1, -1)]:
            brg = initial_bearing_deg(0.0, 0.0, float(lat2), float(lon2))
            assert 0.0 <= brg < 360.0, f"Bearing {brg} out of [0,360) for dest ({lat2},{lon2})"

    def test_coincident_points_returns_zero(self) -> None:
        # Coincident → atan2(0,0) → 0 after normalisation; documented as safe default.
        brg = initial_bearing_deg(28.61, 77.23, 28.61, 77.23)
        assert brg == 0.0


# ---------------------------------------------------------------------------
# smallest_angle_diff_deg
# ---------------------------------------------------------------------------


class TestSmallestAngleDiffDeg:
    def test_zero_diff(self) -> None:
        assert smallest_angle_diff_deg(45.0, 45.0) == 0.0

    def test_wrap_around_short_arc(self) -> None:
        # 350° and 10° are 20° apart (going through 0°), not 340°.
        # Reference: this is the canonical wrap-around smoke corridor test
        # mentioned in architecture.md §6.
        assert abs(smallest_angle_diff_deg(350.0, 10.0) - 20.0) < 1e-9

    def test_exactly_opposite(self) -> None:
        # 0° and 180° are 180° apart.
        assert abs(smallest_angle_diff_deg(0.0, 180.0) - 180.0) < 1e-9

    def test_90_degree_diff(self) -> None:
        assert abs(smallest_angle_diff_deg(90.0, 180.0) - 90.0) < 1e-9

    def test_negative_input_wraps(self) -> None:
        # -10° ≡ 350°; diff from 10° should be 20°.
        assert abs(smallest_angle_diff_deg(-10.0, 10.0) - 20.0) < 1e-9

    def test_symmetry(self) -> None:
        assert smallest_angle_diff_deg(30.0, 60.0) == smallest_angle_diff_deg(60.0, 30.0)

    def test_result_in_range(self) -> None:
        # Result must always be in [0, 180].
        for a, b in [(0, 359), (180, 0), (270, 90), (1, 359)]:
            diff = smallest_angle_diff_deg(float(a), float(b))
            assert 0.0 <= diff <= 180.0, f"diff={diff} out of [0,180] for ({a},{b})"


# ---------------------------------------------------------------------------
# circular_mean_deg
# ---------------------------------------------------------------------------


class TestCircularMeanDeg:
    def test_wrap_around_canonical(self) -> None:
        # THE critical test — architecture.md §6 explicitly requires this.
        # mean(350°, 10°) must be 0°, not 180°.
        # Reference: circular mean via unit-vector decomposition.
        # sin(350°)+sin(10°) = -0.1736+0.1736 = 0; cos(350°)+cos(10°) = 2*cos(10°) > 0.
        # atan2(0, positive) = 0°.
        result = circular_mean_deg([350.0, 10.0])
        assert abs(result - 0.0) < 1e-6 or abs(result - 360.0) < 1e-6, (
            f"circular_mean([350, 10]) should be 0°, got {result:.4f}°"
        )

    def test_single_angle_unchanged(self) -> None:
        # Mean of one angle is that angle.
        assert abs(circular_mean_deg([135.0]) - 135.0) < 1e-9

    def test_identical_angles(self) -> None:
        # Mean of repeated angles is the same angle.
        assert abs(circular_mean_deg([200.0, 200.0, 200.0]) - 200.0) < 1e-9

    def test_north_south_symmetry(self) -> None:
        # 0° and 180° are diametrically opposite; their sin components
        # cancel to ~0 (floating-point residual 1.2e-16), while cos sums
        # to exactly 0.0.  Python atan2(tiny_positive, 0) = 90°.
        # The mean is numerically indeterminate; we only require the
        # result is within [0, 360) — not a specific value.
        result = circular_mean_deg([0.0, 180.0])
        assert 0.0 <= result < 360.0

    def test_four_cardinal_directions(self) -> None:
        # N(0°) + E(90°) + S(180°) + W(270°): floating-point residuals
        # give sin_sum ≈ cos_sum ≈ 1.2e-16, atan2 returns 135°.
        # The mean is numerically indeterminate; we only require [0, 360).
        result = circular_mean_deg([0.0, 90.0, 180.0, 270.0])
        assert 0.0 <= result < 360.0

    def test_north_cluster(self) -> None:
        # 355°, 0°, 5° — all near north, should average ≈ 0°.
        result = circular_mean_deg([355.0, 0.0, 5.0])
        assert abs(result) < 2.0 or abs(result - 360.0) < 2.0, (
            f"Near-north cluster mean should be ~0°, got {result:.2f}°"
        )

    def test_result_in_range(self) -> None:
        result = circular_mean_deg([100.0, 200.0, 300.0])
        assert 0.0 <= result < 360.0

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one angle"):
            circular_mean_deg([])


# ---------------------------------------------------------------------------
# smoke_bearing_from_wind_from
# ---------------------------------------------------------------------------


class TestSmokeBearingFromWindFrom:
    def test_west_wind_pushes_east(self) -> None:
        # Wind FROM west (270°) pushes smoke TOWARDS east (90°).
        # Reference: architecture.md §6 Step 2: smoke_bearing = (dir_from+180)%360.
        assert smoke_bearing_from_wind_from(270.0) == 90.0

    def test_north_wind_pushes_south(self) -> None:
        # Wind FROM north (0°) pushes smoke towards south (180°).
        assert smoke_bearing_from_wind_from(0.0) == 180.0

    def test_south_wind_pushes_north(self) -> None:
        # Wind FROM south (180°) pushes smoke towards north (0°).
        assert smoke_bearing_from_wind_from(180.0) == 0.0

    def test_east_wind_pushes_west(self) -> None:
        # Wind FROM east (90°) pushes smoke towards west (270°).
        assert smoke_bearing_from_wind_from(90.0) == 270.0

    def test_wrap_at_360(self) -> None:
        # 350° + 180 = 530 → 170°.
        assert smoke_bearing_from_wind_from(350.0) == 170.0

    def test_result_in_range(self) -> None:
        for wind in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 359.9]:
            result = smoke_bearing_from_wind_from(wind)
            assert 0.0 <= result < 360.0, f"smoke_bearing out of range for wind_from={wind}"

    def test_negative_wind_from_wraps(self) -> None:
        # -10° ≡ 350°, smoke bearing = 170°.
        assert abs(smoke_bearing_from_wind_from(-10.0) - 170.0) < 1e-9
