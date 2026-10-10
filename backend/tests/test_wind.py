"""Unit tests for regional Open-Meteo wind field fetching and processing."""

import json
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.wind import (
    WindError,
    assign_wind_to_cluster,
    average_wind,
    build_wind_grid,
    fetch_wind_forecast,
    nearest_grid_point,
    parse_wind_forecast,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wind_sample.json"


def test_fixture_file_exists_and_is_labelled() -> None:
    """Ensure the recorded wind test fixture exists and contains fixture label."""
    assert FIXTURE_PATH.is_file(), f"Fixture file not found at {FIXTURE_PATH}"
    content = FIXTURE_PATH.read_text(encoding="utf-8")
    assert "TEST FIXTURE" in content


def test_average_wind_arithmetic_speed_and_circular_direction_wrap_around() -> None:
    """Verify arithmetic mean for speed and circular mean for angular wrap-around.

    350° and 10° must average to 0°, NOT 180°.
    Speed: (10 + 20) / 2 = 15.0 km/h.
    """
    speeds = [10.0, 20.0]
    dirs = [350.0, 10.0]

    avg_speed, avg_dir = average_wind(speeds, dirs)
    assert avg_speed == 15.0
    assert avg_dir == 0.0


def test_average_wind_with_configured_window() -> None:
    """Verify window parameter truncates hourly observations correctly."""
    speeds = [10.0, 20.0, 30.0, 100.0]
    dirs = [0.0, 0.0, 0.0, 180.0]

    # With window=3, the 4th observation (100 km/h, 180°) is ignored
    avg_speed, avg_dir = average_wind(speeds, dirs, window_hours=3)
    assert avg_speed == 20.0
    assert avg_dir == 0.0


def test_average_wind_validation_errors() -> None:
    """Verify validation for empty lists and length mismatch."""
    with pytest.raises(ValueError, match="Cannot average empty"):
        average_wind([], [])

    with pytest.raises(ValueError, match="Length mismatch"):
        average_wind([10.0], [10.0, 20.0])


def test_parse_wind_forecast_from_fixture() -> None:
    """Verify parsing Open-Meteo response using recorded fixture file."""
    raw_content = FIXTURE_PATH.read_text(encoding="utf-8")
    data = json.loads(raw_content)

    grid_map = parse_wind_forecast(data, window_hours=24)
    assert len(grid_map) == 2
    assert (30.0, 75.0) in grid_map
    assert (30.5, 75.5) in grid_map

    # Point 1: speeds [12, 18, 15] -> 15.0 km/h, dirs [350, 0, 10] -> 0.0°
    p1_speed, p1_dir = grid_map[(30.0, 75.0)]
    assert p1_speed == 15.0
    assert p1_dir == 0.0

    # Point 2: speeds [20, 25, 15] -> 20.0 km/h, dirs [90, 95, 85] -> 90.0°
    p2_speed, p2_dir = grid_map[(30.5, 75.5)]
    assert p2_speed == 20.0
    assert p2_dir == 90.0


def test_nearest_grid_point_assignment() -> None:
    """Verify nearest meteorological grid point calculation."""
    candidates = [(30.0, 75.0), (30.5, 75.5), (31.0, 76.0)]

    # Point very close to (30.0, 75.0)
    assert nearest_grid_point(30.02, 75.01, candidates) == (30.0, 75.0)

    # Point closer to (30.5, 75.5)
    assert nearest_grid_point(30.48, 75.52, candidates) == (30.5, 75.5)

    with pytest.raises(ValueError, match="cannot be empty"):
        nearest_grid_point(30.0, 75.0, [])


def test_assign_wind_to_cluster() -> None:
    """Verify enriching a fire cluster with nearest wind field data."""
    grid_wind_map = {
        (30.0, 75.0): (14.5, 315.0),
        (30.5, 75.5): (22.0, 90.0),
    }

    cluster = {
        "clusterId": "30.0000_75.0000",
        "lat": 30.04,
        "lon": 75.02,
        "totalFrp": 50.0,
    }

    enriched = assign_wind_to_cluster(cluster, grid_wind_map)
    assert enriched["windSpeedKmh"] == 14.5
    assert enriched["windDirDeg"] == 315.0
    assert enriched["windGridPoint"] == [30.0, 75.0]


def test_build_wind_grid() -> None:
    """Verify generation of regular sampling grid."""
    grid = build_wind_grid(min_lat=29.0, max_lat=30.0, min_lon=75.0, max_lon=76.0, step_deg=0.5)
    # Lats: 29.0, 29.5, 30.0 (3)
    # Lons: 75.0, 75.5, 76.0 (3)
    # Total = 3 * 3 = 9 points
    assert len(grid) == 9
    assert (29.0, 75.0) in grid
    assert (30.0, 76.0) in grid

    with pytest.raises(ValueError, match="step_deg must be positive"):
        build_wind_grid(29.0, 30.0, 75.0, 76.0, step_deg=-0.1)


def test_fetch_wind_forecast_multi_location_url_and_mock() -> None:
    """Verify fetch_wind_forecast single multi-location GET request."""
    fake_json = json.dumps([
        {
            "latitude": 30.0,
            "longitude": 75.0,
            "hourly": {
                "wind_speed_10m": [10.0],
                "wind_direction_10m": [180.0],
            },
        }
    ]).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = fake_json
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = fetch_wind_forecast([(30.0, 75.0), (30.5, 75.5)])
        assert len(res) == 1
        assert mock_urlopen.call_count == 1

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert "latitude=30.0%2C30.5" in req.full_url or "latitude=30.0,30.5" in req.full_url
        assert "longitude=75.0%2C75.5" in req.full_url or "longitude=75.0,75.5" in req.full_url
        assert "wind_speed_unit=kmh" in req.full_url


def test_fetch_wind_forecast_network_error() -> None:
    """Verify network error handling raises WindError."""
    http_err = urllib.error.HTTPError(
        url="https://api.open-meteo.com/...",
        code=500,
        msg="Internal Error",
        hdrs=MagicMock(),
        fp=BytesIO(b"Server error"),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(WindError, match="Open-Meteo HTTP 500"):
            fetch_wind_forecast([(30.0, 75.0)])


def test_fetch_wind_forecast_validation() -> None:
    """Verify bounds validation on grid_points."""
    with pytest.raises(ValueError, match="cannot be empty"):
        fetch_wind_forecast([])

    too_many = [(30.0 + i * 0.01, 75.0) for i in range(1001)]
    with pytest.raises(ValueError, match="exceeds maximum allowed"):
        fetch_wind_forecast(too_many)
