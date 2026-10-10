"""NASA FIRMS Area API client and CSV parser for DownWind.

Fetches satellite fire detection data from NASA FIRMS Area API using Python
standard library urllib and parses CSV detections, filtering low-confidence
observations and converting UTC acquisition timestamps to Indian Standard Time (IST).
"""

from __future__ import annotations

import csv
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

# Base endpoint for FIRMS Area CSV API
FIRMS_AREA_CSV_BASE_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Indian Standard Time offset (UTC+5:30)
IST_TIMEZONE: timezone = timezone(timedelta(hours=5, minutes=30))


class FirmsError(Exception):
    """Raised when FIRMS API requests or data processing fail."""


def fetch_firms_csv(
    map_key: str,
    source: str,
    area: str,
    day_range: int = 1,
    date: str | None = None,
    timeout: float = 30.0,
) -> str:
    """Fetch raw CSV data from the NASA FIRMS Area API.

    Args:
        map_key: NASA FIRMS MAP_KEY credential (never logged or hardcoded).
        source: Sensor source (e.g. 'VIIRS_NOAA20_NRT', 'VIIRS_SNPP_NRT', 'MODIS_NRT').
        area: Bounding box string 'west,south,east,north' or 'world'.
        day_range: Number of days (1 to 5).
        date: Optional specific acquisition date (YYYY-MM-DD). If omitted, most recent.
        timeout: Network request timeout in seconds.

    Returns:
        Raw CSV text response from NASA FIRMS.

    Raises:
        ValueError: If map_key is empty or day_range is outside [1, 5].
        FirmsError: If HTTP request fails or times out.
    """
    clean_key = map_key.strip()
    if not clean_key:
        raise ValueError("MAP_KEY is required and cannot be empty.")

    if not (1 <= day_range <= 5):
        raise ValueError(f"day_range must be between 1 and 5, got {day_range}.")

    clean_source = source.strip()
    clean_area = area.strip()

    if date:
        clean_date = date.strip()
        url = (
            f"{FIRMS_AREA_CSV_BASE_URL}/{clean_key}/{clean_source}/"
            f"{clean_area}/{day_range}/{clean_date}"
        )
    else:
        url = (
            f"{FIRMS_AREA_CSV_BASE_URL}/{clean_key}/{clean_source}/"
            f"{clean_area}/{day_range}"
        )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DownWind/1.0 (+https://github.com/harshsingh2275/DownWind)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw_bytes: bytes = response.read()
            return raw_bytes.decode("utf-8")
    except urllib.error.HTTPError as exc:
        # Note: Do not include `url` directly in the error message to prevent leaking MAP_KEY.
        raise FirmsError(
            f"FIRMS HTTP error {exc.code} for source='{clean_source}', area='{clean_area}': "
            f"{exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise FirmsError(
            f"FIRMS network error for source='{clean_source}', area='{clean_area}': "
            f"{exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise FirmsError(
            f"FIRMS request timed out after {timeout}s for source='{clean_source}'"
        ) from exc
    except Exception as exc:
        raise FirmsError(
            f"Unexpected error fetching FIRMS data for source='{clean_source}': {exc}"
        ) from exc


def parse_firms_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse FIRMS CSV text into structured fire detection dictionaries.

    Filters out rows with confidence 'low' (case-insensitive).
    Converts acq_date and acq_time (UTC HHMM) to a timezone-aware UTC datetime
    and an IST calendar day (YYYY-MM-DD).

    Args:
        csv_text: Raw CSV string from FIRMS API or recorded fixture.

    Returns:
        List of detection dicts with fields:
        - lat: float
        - lon: float
        - latitude: float
        - longitude: float
        - frp: float
        - confidence: str
        - acq_utc: datetime (UTC timezone-aware)
        - ist_day: str (YYYY-MM-DD in IST)
        - satellite: str
        - instrument: str
    """
    if not csv_text or not csv_text.strip():
        return []

    # Filter out empty lines and fixture comment headers (lines starting with #)
    clean_lines = [
        line.strip()
        for line in csv_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not clean_lines:
        return []

    reader = csv.DictReader(clean_lines)
    detections: list[dict[str, Any]] = []

    for row in reader:
        # Confidence check: drop low confidence detections
        conf_raw = (row.get("confidence") or "").strip().lower()
        if conf_raw == "low":
            continue

        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
        except (KeyError, ValueError):
            continue

        # Fire Radiative Power (FRP)
        try:
            frp = float(row["frp"]) if row.get("frp") else 0.0
        except ValueError:
            frp = 0.0

        # Acquisition date (YYYY-MM-DD) and time (HHMM UTC)
        acq_date_str = (row.get("acq_date") or "").strip()
        acq_time_raw = (row.get("acq_time") or "").replace(":", "").strip()

        if not acq_date_str or not acq_time_raw:
            continue

        try:
            year, month, day = map(int, acq_date_str.split("-"))
            time_padded = acq_time_raw.zfill(4)
            hour = int(time_padded[:2])
            minute = int(time_padded[2:4])
            acq_utc = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            continue

        # Convert UTC datetime to IST calendar date string (YYYY-MM-DD)
        ist_datetime = acq_utc.astimezone(IST_TIMEZONE)
        ist_day = ist_datetime.strftime("%Y-%m-%d")

        detections.append(
            {
                "lat": lat,
                "lon": lon,
                "latitude": lat,
                "longitude": lon,
                "frp": frp,
                "confidence": conf_raw,
                "acq_utc": acq_utc,
                "ist_day": ist_day,
                "satellite": (row.get("satellite") or "").strip(),
                "instrument": (row.get("instrument") or "").strip(),
            }
        )

    return detections
