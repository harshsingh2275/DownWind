"""Unit tests for backend/tools/run_local.py (T-027)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.run_local import (
    DEFAULT_ARCHIVE_SOURCE,
    DEFAULT_FALLBACK_ARCHIVE_DATE,
    get_map_key,
    run_pipeline,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "firms_sample.csv"


def test_missing_env_var_returns_error_and_prints_instructions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify clean exit and helpful instructions when FIRMS_MAP_KEY is missing."""
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    monkeypatch.delenv("MAP_KEY", raising=False)

    key = get_map_key()
    assert key is None

    err = capsys.readouterr().err
    assert "NASA FIRMS MAP_KEY is not set" in err
    assert "$env:FIRMS_MAP_KEY" in err
    assert "export FIRMS_MAP_KEY" in err

    result = run_pipeline()
    assert result["success"] is False
    assert result["error"] == "MISSING_MAP_KEY"


def test_get_map_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify get_map_key reads FIRMS_MAP_KEY or MAP_KEY."""
    fake_key = "abc1234567890abcdef1234567890abc"
    monkeypatch.setenv("FIRMS_MAP_KEY", fake_key)
    assert get_map_key() == fake_key

    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    monkeypatch.setenv("MAP_KEY", fake_key)
    assert get_map_key() == fake_key


def test_run_pipeline_with_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify full pipeline runs end-to-end using local fixture."""
    result = run_pipeline(fixture_path=FIXTURE_PATH)
    assert result["success"] is True
    assert result["raw_detections"] == 4
    assert result["in_region_detections"] == 4
    assert result["clusters_count"] == 4
    assert result["total_frp"] > 0

    out = capsys.readouterr().out
    assert "DOWNWIND PIPELINE EXECUTION SUMMARY" in out
    assert "Stage 1/5" in out
    assert "Stage 5/5" in out


DUMMY_WIND_DATA = [
    {
        "latitude": 30.0,
        "longitude": 75.0,
        "hourly": {
            "wind_speed_10m": [15.0] * 24,
            "wind_direction_10m": [315.0] * 24,
        },
    }
]


def test_run_pipeline_never_leaks_key_in_stdout_or_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify MAP_KEY is never printed or logged under any circumstance."""
    secret_key = "super_secret_test_key_xyz12345"
    monkeypatch.setenv("FIRMS_MAP_KEY", secret_key)

    with patch("tools.run_local.fetch_firms_csv", return_value=""), patch(
        "tools.run_local.fetch_wind_data", return_value=DUMMY_WIND_DATA
    ):
        run_pipeline(map_key=secret_key)

    captured = capsys.readouterr()
    assert secret_key not in captured.out
    assert secret_key not in captured.err


def test_run_pipeline_archive_fallback_when_no_nrt_fires(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify pipeline automatically switches to archive date if NRT has 0 fires."""
    secret_key = "dummy_valid_test_key_1234567890"

    fixture_csv = FIXTURE_PATH.read_text(encoding="utf-8")

    # First call (NRT) returns empty CSV, second call (Archive fallback) returns fixture CSV
    mock_fetch = MagicMock(side_effect=["", fixture_csv])

    with patch("tools.run_local.fetch_firms_csv", mock_fetch), patch(
        "tools.run_local.fetch_wind_data", return_value=DUMMY_WIND_DATA
    ):
        result = run_pipeline(map_key=secret_key, date=None)

    assert result["success"] is True
    assert result["used_fallback_archive"] is True
    assert result["source"] == DEFAULT_ARCHIVE_SOURCE
    assert result["date"] == DEFAULT_FALLBACK_ARCHIVE_DATE
    assert result["in_region_detections"] == 4

    out = capsys.readouterr().out
    assert "No active fires detected in Near Real-Time (NRT) today" in out
    expected_msg = (
        f"Switching to historical stubble burning archive date: {DEFAULT_FALLBACK_ARCHIVE_DATE}"
    )
    assert expected_msg in out
    assert secret_key not in out
