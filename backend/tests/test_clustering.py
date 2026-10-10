"""Unit tests for configuration values and spatial grid clustering."""

from datetime import datetime, timezone

from src.clustering import cluster_detections, get_grid_cell_id
from src.config import (
    ALERT_COOLDOWN_HOURS,
    ANGLE_TOLERANCE_DEG,
    ATTENUATION,
    CLUSTER_GRID_DEG,
    MIN_CONFIDENCE,
    MIN_WIND_KMH,
    TRAVEL_HOURS,
)


def test_config_tunable_values_match_architecture_section_6() -> None:
    """Verify all 7 tunable values from architecture.md section 6 exist and match."""
    assert CLUSTER_GRID_DEG == 0.05
    assert MIN_CONFIDENCE == "nominal"
    assert ANGLE_TOLERANCE_DEG == 25.0
    assert TRAVEL_HOURS == 24.0
    assert ATTENUATION == 0.5
    assert MIN_WIND_KMH == 1.0
    assert ALERT_COOLDOWN_HOURS == 12.0


def test_empty_input_returns_empty_output() -> None:
    """Verify empty detections list returns empty cluster list."""
    assert cluster_detections([]) == []


def test_same_cell_merge() -> None:
    """Verify multiple detections in the same grid cell merge correctly."""
    # Base cell: 30.00 to 30.05 lat, 75.00 to 75.05 lon
    t1 = datetime(2024, 10, 31, 8, 0, tzinfo=timezone.utc)
    t2 = datetime(2024, 10, 31, 10, 30, tzinfo=timezone.utc)
    t3 = datetime(2024, 10, 31, 9, 15, tzinfo=timezone.utc)

    detections = [
        {"lat": 30.01, "lon": 75.01, "frp": 10.0, "acq_utc": t1},
        {"lat": 30.02, "lon": 75.02, "frp": 30.0, "acq_utc": t2},
        {"lat": 30.03, "lon": 75.03, "frp": 20.0, "acq_utc": t3},
    ]

    clusters = cluster_detections(detections, grid_deg=0.05)
    assert len(clusters) == 1

    c = clusters[0]
    assert c["clusterId"] == "30.0000_75.0000"
    assert c["count"] == 3
    assert c["totalFrp"] == 60.0
    assert c["maxFrp"] == 30.0

    # FRP-weighted centroid:
    # lat: (30.01*10 + 30.02*30 + 30.03*20) / 60 = 1801.3 / 60 = 30.02167
    # lon: (75.01*10 + 75.02*30 + 75.03*20) / 60 = 4501.3 / 60 = 75.02167
    assert round(c["centroid"]["lat"], 4) == 30.0217
    assert round(c["centroid"]["lon"], 4) == 75.0217
    assert c["lat"] == c["centroid"]["lat"]
    assert c["lon"] == c["centroid"]["lon"]

    # First and last seen
    assert c["firstSeen"] == "2024-10-31T08:00:00Z"
    assert c["lastSeen"] == "2024-10-31T10:30:00Z"
    assert c["firstSeenUtc"] == c["firstSeen"]
    assert c["lastSeenUtc"] == c["lastSeen"]


def test_separate_cells() -> None:
    """Verify points in distinct cells produce distinct clusters."""
    detections = [
        {"lat": 30.01, "lon": 75.01, "frp": 10.0, "acq_utc": "2024-10-31T08:00:00Z"},
        # Lat > 30.05 moves into next cell
        {"lat": 30.06, "lon": 75.01, "frp": 15.0, "acq_utc": "2024-10-31T08:30:00Z"},
        # Lon > 75.05 moves into next cell
        {"lat": 30.01, "lon": 75.07, "frp": 25.0, "acq_utc": "2024-10-31T09:00:00Z"},
    ]

    clusters = cluster_detections(detections, grid_deg=0.05)
    assert len(clusters) == 3

    ids = [c["clusterId"] for c in clusters]
    assert "30.0000_75.0000" in ids
    assert "30.0500_75.0000" in ids
    assert "30.0000_75.0500" in ids


def test_deterministic_cluster_ids_and_ordering() -> None:
    """Verify cluster IDs and list output are deterministic regardless of input order."""
    d1 = {"lat": 30.01, "lon": 75.01, "frp": 10.0}
    d2 = {"lat": 31.52, "lon": 76.12, "frp": 20.0}
    d3 = {"lat": 29.88, "lon": 74.33, "frp": 5.0}

    order_a = cluster_detections([d1, d2, d3], grid_deg=0.05)
    order_b = cluster_detections([d3, d1, d2], grid_deg=0.05)
    order_c = cluster_detections([d2, d3, d1], grid_deg=0.05)

    assert [c["clusterId"] for c in order_a] == [c["clusterId"] for c in order_b]
    assert [c["clusterId"] for c in order_a] == [c["clusterId"] for c in order_c]

    # Check cell ID formula directly
    cid = get_grid_cell_id(30.02, 75.03, grid_deg=0.05)
    assert cid == "30.0000_75.0000"


def test_zero_frp_uses_simple_mean() -> None:
    """Verify fallback to simple arithmetic mean when all FRP values are 0."""
    detections = [
        {"lat": 30.01, "lon": 75.01, "frp": 0.0},
        {"lat": 30.03, "lon": 75.03, "frp": 0.0},
    ]
    clusters = cluster_detections(detections, grid_deg=0.05)
    assert len(clusters) == 1
    assert clusters[0]["centroid"]["lat"] == 30.02
    assert clusters[0]["centroid"]["lon"] == 75.02
    assert clusters[0]["totalFrp"] == 0.0
