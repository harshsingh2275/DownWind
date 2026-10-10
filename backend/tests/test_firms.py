"""Unit tests for NASA FIRMS Area API client and parser."""

import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.firms import (
    FirmsError,
    fetch_firms_csv,
    parse_firms_csv,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "firms_sample.csv"


def test_fixture_file_exists_and_is_labelled() -> None:
    """Ensure the recorded test fixture exists and contains fixture label."""
    assert FIXTURE_PATH.is_file(), f"Fixture file not found at {FIXTURE_PATH}"
    content = FIXTURE_PATH.read_text(encoding="utf-8")
    assert "TEST FIXTURE" in content


def test_parse_firms_csv_from_recorded_fixture() -> None:
    """Verify parsing against the recorded test fixture."""
    csv_text = FIXTURE_PATH.read_text(encoding="utf-8")
    detections = parse_firms_csv(csv_text)

    # In the fixture:
    # Row 1: nominal (kept)
    # Row 2: high (kept)
    # Row 3: low (dropped)
    # Row 4: nominal (kept)
    # Row 5: LOW (dropped)
    # Row 6: high (kept)
    assert len(detections) == 4

    # All returned detections must have non-low confidence
    for det in detections:
        assert det["confidence"] != "low"
        assert isinstance(det["lat"], float)
        assert isinstance(det["lon"], float)
        assert isinstance(det["frp"], float)
        assert isinstance(det["acq_utc"], datetime)
        assert det["acq_utc"].tzinfo == timezone.utc
        assert isinstance(det["ist_day"], str)


def test_utc_2130_maps_to_next_ist_day() -> None:
    """Test specifically that UTC 21:30 maps to the next IST day.

    2024-10-31 21:30 UTC + 05:30 IST = 2024-11-01 03:00 IST.
    """
    sample_csv = (
        "latitude,longitude,acq_date,acq_time,confidence,frp\n"
        "30.50,75.50,2024-10-31,2130,nominal,12.5\n"
    )
    detections = parse_firms_csv(sample_csv)
    assert len(detections) == 1
    det = detections[0]

    assert det["acq_utc"] == datetime(2024, 10, 31, 21, 30, tzinfo=timezone.utc)
    # Verification: 21:30 UTC is next day in IST
    assert det["ist_day"] == "2024-11-01"


def test_utc_morning_maps_to_same_ist_day() -> None:
    """Test that UTC 08:15 maps to the same IST day.

    2024-10-31 08:15 UTC + 05:30 IST = 2024-10-31 13:45 IST.
    """
    sample_csv = (
        "latitude,longitude,acq_date,acq_time,confidence,frp\n"
        "31.10,75.20,2024-10-31,0815,high,25.0\n"
    )
    detections = parse_firms_csv(sample_csv)
    assert len(detections) == 1
    det = detections[0]

    assert det["acq_utc"] == datetime(2024, 10, 31, 8, 15, tzinfo=timezone.utc)
    assert det["ist_day"] == "2024-10-31"


def test_low_confidence_dropped_case_insensitively() -> None:
    """Ensure rows with confidence 'low', 'Low', 'LOW' are dropped."""
    sample_csv = (
        "latitude,longitude,acq_date,acq_time,confidence,frp\n"
        "30.1,75.1,2024-10-31,1000,low,10.0\n"
        "30.2,75.2,2024-10-31,1000,LOW,10.0\n"
        "30.3,75.3,2024-10-31,1000,Low,10.0\n"
        "30.4,75.4,2024-10-31,1000,nominal,10.0\n"
    )
    detections = parse_firms_csv(sample_csv)
    assert len(detections) == 1
    assert detections[0]["lat"] == 30.4


def test_empty_and_comment_csv() -> None:
    """Ensure empty CSV or comment-only CSV returns an empty list."""
    assert parse_firms_csv("") == []
    assert parse_firms_csv("   \n\n  ") == []
    assert parse_firms_csv("# This is a comment\n# Another comment\n") == []


def test_fetch_firms_csv_success_url_structure() -> None:
    """Verify fetch_firms_csv builds correct URL and headers."""
    fake_csv_data = b"latitude,longitude,acq_date,acq_time,confidence,frp\n"
    secret_key = "test_secret_map_key_123"

    mock_resp = MagicMock()
    mock_resp.read.return_value = fake_csv_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = fetch_firms_csv(
            map_key=secret_key,
            source="VIIRS_NOAA20_NRT",
            area="73.8,27.6,77.6,32.5",
            day_range=2,
            date="2024-10-31",
        )
        assert result == fake_csv_data.decode("utf-8")
        assert mock_urlopen.call_count == 1

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        expected_url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{secret_key}/VIIRS_NOAA20_NRT/73.8,27.6,77.6,32.5/2/2024-10-31"
        )
        assert req.full_url == expected_url


def test_fetch_firms_csv_never_logs_or_leaks_map_key_on_error() -> None:
    """Verify that network errors do NOT expose or leak MAP_KEY in exception messages."""
    secret_key = "super_confidential_key_999"

    http_error = urllib.error.HTTPError(
        url="https://firms.modaps.eosdis.nasa.gov/api/area/csv/secret/...",
        code=403,
        msg="Forbidden",
        hdrs=MagicMock(),
        fp=BytesIO(b"Unauthorized"),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(FirmsError) as exc_info:
            fetch_firms_csv(
                map_key=secret_key,
                source="VIIRS_NOAA20_NRT",
                area="world",
                day_range=1,
            )

        error_message = str(exc_info.value)
        assert secret_key not in error_message
        assert "HTTP error 403" in error_message


def test_fetch_firms_csv_validation() -> None:
    """Validate map_key presence and day_range bounds."""
    with pytest.raises(ValueError, match="MAP_KEY is required"):
        fetch_firms_csv(map_key="", source="VIIRS_NOAA20_NRT", area="world")

    with pytest.raises(ValueError, match="day_range must be between 1 and 5"):
        fetch_firms_csv(map_key="valid_key", source="VIIRS_NOAA20_NRT", area="world", day_range=0)

    with pytest.raises(ValueError, match="day_range must be between 1 and 5"):
        fetch_firms_csv(map_key="valid_key", source="VIIRS_NOAA20_NRT", area="world", day_range=6)
