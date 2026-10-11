"""Ingest Lambda handler for DownWind (T-031).

Responsibility:
  - Read the NASA FIRMS MAP_KEY from SSM Parameter Store (cached across
    warm invocations via module-level variable).
  - Run the full pipeline:
      fetch → region filter → cluster → wind → impact
  - Write Cluster and Impact records to DynamoDB idempotently (PutItem
    with deterministic PKs, so re-running the same data = same items).
  - On high-severity city impact that has passed the alert cooldown,
    publish to the per-city SNS topic.
  - On any unrecoverable error, log a structured error message (secrets
    never included) and re-raise so Lambda marks the invocation as FAILED.

Secrets hygiene:
  - The MAP_KEY value is NEVER logged, printed, or included in any
    exception message or structured log field.
  - Only the SSM parameter *name* (the path) is referenced in logs.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# boto3 is NOT imported at module level — it is only available in the Lambda
# runtime.  Importing lazily inside factory functions lets unit tests patch
# boto3.client / boto3.resource before any real import happens.
#
# Usage pattern:
#   with patch('boto3.client', return_value=mock_ssm): ...
from src.clustering import cluster_detections
from src.config import ALERT_COOLDOWN_HOURS
from src.firms import FirmsError, fetch_firms_csv, parse_firms_csv
from src.impact import compute_impact
from src.region import is_point_in_geojson, load_region_boundary
from src.wind import (
    assign_wind_to_cluster,
    build_wind_grid,
    fetch_wind_data,
    parse_wind_forecast,
)

# ---------------------------------------------------------------------------
# Region / IST constants
# ---------------------------------------------------------------------------
IST_TIMEZONE: timezone = timezone(timedelta(hours=5, minutes=30))

# Bounding box for Punjab + Haryana region (degrees)
REGION_MIN_LAT: float = 27.5
REGION_MAX_LAT: float = 32.5
REGION_MIN_LON: float = 73.5
REGION_MAX_LON: float = 78.5
REGION_AREA: str = f"{REGION_MIN_LON},{REGION_MIN_LAT},{REGION_MAX_LON},{REGION_MAX_LAT}"

# FIRMS source and query parameters
FIRMS_SOURCE: str = "VIIRS_NOAA20_NRT"
FIRMS_DAY_RANGE: int = 1

# Per-city SNS topic naming convention (must match template.yaml IAM)
SNS_CITY_TOPIC_PREFIX: str = "downwind-city-"

# ---------------------------------------------------------------------------
# Module-level SSM/boto3 clients (re-used across warm invocations)
# ---------------------------------------------------------------------------
_ssm_client: Any = None
_dynamo_resource: Any = None
_sns_client: Any = None

# Cached SSM key value: populated on first cold start, reused on warm calls
_cached_firms_key: str | None = None


def _get_ssm_client() -> Any:
    global _ssm_client
    if _ssm_client is None:
        import boto3  # noqa: PLC0415 — lazy import for Lambda runtime only
        _ssm_client = boto3.client("ssm")
    return _ssm_client


def _get_dynamo_resource() -> Any:
    global _dynamo_resource
    if _dynamo_resource is None:
        import boto3  # noqa: PLC0415 — lazy import for Lambda runtime only
        _dynamo_resource = boto3.resource("dynamodb")
    return _dynamo_resource


def _get_sns_client() -> Any:
    global _sns_client
    if _sns_client is None:
        import boto3  # noqa: PLC0415 — lazy import for Lambda runtime only
        _sns_client = boto3.client("sns")
    return _sns_client


# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------
def _log(level: str, message: str, **kwargs: Any) -> None:
    """Emit a JSON-structured log line to stderr.

    The FIRMS MAP_KEY value is explicitly excluded from all log calls at the
    call sites.  kwargs must never include the key value.
    """
    entry: dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "level": level,
        "message": message,
        **kwargs,
    }
    print(json.dumps(entry, default=str), flush=True)


# ---------------------------------------------------------------------------
# SSM key retrieval (cached)
# ---------------------------------------------------------------------------
def _get_firms_key() -> str:
    """Retrieve the FIRMS MAP_KEY from SSM Parameter Store.

    The value is cached in the module-level variable after the first call
    so warm Lambda invocations skip the SSM network round-trip.

    Returns:
        The decrypted MAP_KEY string.

    Raises:
        RuntimeError: If the SSM parameter name env var is not set, or if
                      SSM retrieval fails.
    """
    global _cached_firms_key

    if _cached_firms_key is not None:
        return _cached_firms_key

    param_name = os.environ.get("FIRMS_KEY_PARAMETER_NAME", "").strip()
    if not param_name:
        raise RuntimeError(
            "FIRMS_KEY_PARAMETER_NAME environment variable is not set. "
            "Check the SAM template Globals/Environment."
        )

    _log("INFO", "Fetching FIRMS key from SSM", ssm_param_name=param_name)

    ssm = _get_ssm_client()
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        key_value: str = response["Parameter"]["Value"]
    except Exception as exc:
        # Do NOT include exc details that may leak context about the key value
        raise RuntimeError(
            f"Failed to retrieve FIRMS key from SSM parameter '{param_name}': "
            f"{type(exc).__name__}"
        ) from exc

    if not key_value.strip():
        raise RuntimeError(
            f"SSM parameter '{param_name}' is empty — check the stored value."
        )

    _cached_firms_key = key_value
    _log("INFO", "FIRMS key retrieved successfully (value not logged)", ssm_param_name=param_name)
    return _cached_firms_key


# ---------------------------------------------------------------------------
# DynamoDB writers
# ---------------------------------------------------------------------------
def _ttl_epoch(days: int = 7) -> int:
    """Compute Unix epoch TTL value for 'days' from now."""
    ttl_days = int(os.environ.get("DYNAMO_TTL_DAYS", str(days)))
    return int(time.time()) + ttl_days * 86400


def _write_clusters(
    clusters: list[dict[str, Any]],
    ist_day: str,
    table_name: str,
) -> tuple[int, int]:
    """Write cluster records to DynamoDB (idempotent PutItem).

    Args:
        clusters: List of cluster dicts from cluster_detections + wind assignment.
        ist_day: IST calendar date string (YYYY-MM-DD), used as partition key.
        table_name: DynamoDB table name from environment.

    Returns:
        Tuple of (written_count, failed_count).
    """
    dynamo = _get_dynamo_resource()
    table = dynamo.Table(table_name)
    ttl_val = _ttl_epoch()

    written = 0
    failed = 0

    for cluster in clusters:
        item: dict[str, Any] = {
            "day": ist_day,
            "clusterId": cluster["clusterId"],
            "lat": str(cluster.get("lat", "")),
            "lon": str(cluster.get("lon", "")),
            "count": cluster.get("count", 0),
            "totalFrp": str(cluster.get("totalFrp", 0.0)),
            "maxFrp": str(cluster.get("maxFrp", 0.0)),
            "firstSeenUtc": cluster.get("firstSeenUtc", ""),
            "lastSeenUtc": cluster.get("lastSeenUtc", ""),
            "windSpeedKmh": str(cluster.get("windSpeedKmh", 0.0)),
            "windDirDeg": str(cluster.get("windDirDeg", 0.0)),
            "ttl": ttl_val,
        }
        try:
            table.put_item(Item=item)
            written += 1
        except Exception as exc:
            failed += 1
            _log(
                "ERROR",
                "Failed to write cluster to DynamoDB",
                cluster_id=cluster.get("clusterId"),
                error_type=type(exc).__name__,
            )

    return written, failed


def _write_impact(
    impact_records: list[dict[str, Any]],
    ist_day: str,
    table_name: str,
) -> tuple[int, int]:
    """Write impact records to DynamoDB (idempotent PutItem).

    Args:
        impact_records: List of city-impact dicts from compute_impact().
        ist_day: IST calendar date string (YYYY-MM-DD), partition key.
        table_name: DynamoDB table name from environment.

    Returns:
        Tuple of (written_count, failed_count).
    """
    dynamo = _get_dynamo_resource()
    table = dynamo.Table(table_name)
    ttl_val = _ttl_epoch()

    written = 0
    failed = 0

    for record in impact_records:
        city_id = record["cityId"]
        try:
            # Use update_item to update impact metrics WITHOUT wiping out lastAlertedAtUtc
            table.update_item(
                Key={"day": ist_day, "cityId": city_id},
                UpdateExpression=(
                    "SET cityName = :cn, nClusters = :nc, totalFrp = :tf, "
                    "nearestKm = :nk, minEtaHours = :me, severity = :sev, "
                    "affectedByClusterIds = :cl, #ttl_attr = :ttl"
                ),
                ExpressionAttributeNames={
                    "#ttl_attr": "ttl",
                },
                ExpressionAttributeValues={
                    ":cn": record.get("cityName", ""),
                    ":nc": record.get("nClusters", 0),
                    ":tf": str(record.get("totalFrp", 0.0)),
                    ":nk": str(record.get("nearestKm", 0.0)),
                    ":me": str(record.get("minEtaHours", 0.0)),
                    ":sev": record.get("severity", "Low"),
                    ":cl": record.get("affectedByClusterIds", []),
                    ":ttl": ttl_val,
                },
            )
            written += 1
        except Exception as exc:
            failed += 1
            _log(
                "ERROR",
                "Failed to write impact to DynamoDB",
                city_id=city_id,
                error_type=type(exc).__name__,
            )

    return written, failed


# ---------------------------------------------------------------------------
# SNS alert publishing with conditional DynamoDB lock (T-037)
# ---------------------------------------------------------------------------
def _attempt_claim_alert(
    city_id: str,
    ist_day: str,
    impact_table_name: str,
    now_utc_iso: str,
) -> bool:
    """Atomically claim the alert right for a city using a conditional DynamoDB update.

    Returns True if this invocation successfully acquired the alert lock;
    returns False if the city is inside the cooldown window or another concurrent run
    already claimed the alert.

    Condition:
      attribute_not_exists(lastAlertedAtUtc) OR lastAlertedAtUtc < :cutoff
    """
    now_dt = datetime.fromisoformat(now_utc_iso.replace("Z", "+00:00"))
    cutoff_iso = (now_dt - timedelta(hours=ALERT_COOLDOWN_HOURS)).isoformat()

    dynamo = _get_dynamo_resource()
    table = dynamo.Table(impact_table_name)

    try:
        table.update_item(
            Key={"day": ist_day, "cityId": city_id},
            UpdateExpression="SET lastAlertedAtUtc = :now",
            ConditionExpression=(
                "attribute_not_exists(lastAlertedAtUtc) OR lastAlertedAtUtc < :cutoff"
            ),
            ExpressionAttributeValues={
                ":now": now_utc_iso,
                ":cutoff": cutoff_iso,
            },
        )
        return True
    except Exception as exc:
        exc_name = type(exc).__name__
        error_code = ""
        if hasattr(exc, "response") and isinstance(exc.response, dict):
            error_code = exc.response.get("Error", {}).get("Code", "")

        if (
            exc_name == "ConditionalCheckFailedException"
            or error_code == "ConditionalCheckFailedException"
        ):
            _log(
                "INFO",
                "Alert suppressed by cooldown or concurrent claim",
                city_id=city_id,
                day=ist_day,
            )
            return False

        _log(
            "WARN",
            "Conditional DynamoDB update failed; skipping alert to prevent over-alerting",
            city_id=city_id,
            error_type=exc_name,
            error=str(exc),
        )
        return False


def _publish_city_alert(
    city_id: str,
    city_name: str,
    severity: str,
    ist_day: str,
    n_clusters: int,
    total_frp: float,
    nearest_km: float,
    min_eta_hours: float,
    account_id: str = "",
    region: str = "",
) -> None:
    """Publish a smoke-path alert to the per-city SNS topic."""
    env = os.environ.get("ENVIRONMENT", "prod")
    prefix = os.environ.get("CITY_TOPIC_PREFIX")
    if prefix:
        topic_arn = f"{prefix}{city_id}-{env}"
    else:
        region = region or os.environ.get("AWS_REGION", "ap-south-1")
        # account_id must come from the caller (extracted from ops_topic_arn ARN)
        # or AWS_ACCOUNT_ID env var. Never hardcoded in source code.
        account_id = account_id or os.environ.get("AWS_ACCOUNT_ID", "")
        if not account_id:
            _log(
                "WARN",
                "Cannot construct city topic ARN: no account_id available",
                city_id=city_id,
            )
            return
        topic_arn = f"arn:aws:sns:{region}:{account_id}:downwind-city-{city_id}-{env}"

    site_url = os.environ.get("SITE_URL", "https://downwind.local")

    subject = f"[DownWind] High Smoke Alert for {city_name} — {ist_day}"
    body = (
        f"DownWind Smoke Alert\n\n"
        f"City: {city_name}\n"
        f"Severity: {severity} (Estimate)\n"
        f"Date: {ist_day}\n"
        f"Estimated Smoke Arrival (ETA): {min_eta_hours:.1f} hours\n"
        f"Active Fire Clusters: {n_clusters}\n"
        f"Total Fire Radiative Power: {total_frp:.1f} MW\n"
        f"Distance to Nearest Cluster: {nearest_km:.0f} km\n\n"
        "This advisory is an automated smoke plume estimate derived from satellite "
        "fire detections and wind forecast models. It is indicative only.\n\n"
        f"View live map and full impact report:\n{site_url}\n\n"
        "To unsubscribe, use the link provided below by AWS SNS."
    )
    try:
        sns = _get_sns_client()
        sns.publish(TopicArn=topic_arn, Subject=subject[:100], Message=body)
        _log(
            "INFO",
            "SNS alert published",
            city_id=city_id,
            severity=severity,
        )
    except Exception as exc:
        _log(
            "WARN",
            "SNS alert publish failed (non-fatal)",
            city_id=city_id,
            error_type=type(exc).__name__,
        )


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------
def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Ingest Lambda entry point.

    Triggered by EventBridge on a configurable schedule.  Runs the full
    pipeline and returns a summary dict.  Raises on unrecoverable errors so
    Lambda marks the invocation as FAILED (triggering CloudWatch alarm).

    Returns:
        dict with keys: day (IST date), clusters_written, impact_written,
        alerts_sent, partial_failures (int).

    Raises:
        RuntimeError: For unrecoverable pipeline failures (triggers Lambda error).
    """
    start_ts = time.time()
    _log("INFO", "Ingest Lambda started", event_source=event.get("source", "unknown"))

    # ── 0. Environment variables ──────────────────────────────────────────
    clusters_table = os.environ.get("CLUSTERS_TABLE", "")
    impact_table = os.environ.get("IMPACT_TABLE", "")
    ops_topic_arn = os.environ.get("OPS_TOPIC_ARN", "")

    if not clusters_table or not impact_table:
        raise RuntimeError(
            "CLUSTERS_TABLE and IMPACT_TABLE environment variables must be set."
        )

    # Resolve account ID and region for per-city SNS topic ARN construction
    aws_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "ap-south-1"))
    # Account ID: extract from ops_topic_arn if available, else fall back to STS
    aws_account_id = ""
    if ops_topic_arn and ops_topic_arn.startswith("arn:"):
        parts = ops_topic_arn.split(":")
        if len(parts) >= 5:
            aws_account_id = parts[4]

    # ── 1. Retrieve FIRMS key (cached across warm invocations) ────────────
    try:
        firms_key = _get_firms_key()
    except RuntimeError as exc:
        _log("ERROR", "SSM key retrieval failed", error=str(exc))
        raise

    # ── 2. Target date and source ─────────────────────────────────────────
    custom_date: str | None = event.get("date")
    custom_source: str | None = event.get("source")
    if custom_date:
        ist_day = custom_date.strip()
        firms_source = custom_source.strip() if custom_source else "VIIRS_NOAA20_SP"
        firms_date: str | None = ist_day
        _log("INFO", "Processing custom archive date", ist_day=ist_day, source=firms_source)
    else:
        ist_now = datetime.now(tz=IST_TIMEZONE)
        ist_day = ist_now.strftime("%Y-%m-%d")
        firms_source = FIRMS_SOURCE
        firms_date = None
        _log("INFO", "Processing IST day", ist_day=ist_day)

    # ── 3. Fetch FIRMS CSV ────────────────────────────────────────────────
    try:
        _log("INFO", "Fetching FIRMS data", source=firms_source, area=REGION_AREA)
        raw_csv = fetch_firms_csv(
            map_key=firms_key,
            source=firms_source,
            area=REGION_AREA,
            day_range=FIRMS_DAY_RANGE,
            date=firms_date,
        )
    except FirmsError as exc:
        _log("ERROR", "FIRMS fetch failed", error=str(exc))
        raise RuntimeError(f"FIRMS fetch failed: {exc}") from exc

    # ── 4. Parse + low-confidence filter ─────────────────────────────────
    detections = parse_firms_csv(raw_csv)
    _log("INFO", "FIRMS CSV parsed", total_detections=len(detections))

    if not detections:
        _log("WARN", "No fire detections found after filtering; nothing to write")
        return {
            "day": ist_day,
            "clusters_written": 0,
            "impact_written": 0,
            "alerts_sent": 0,
            "partial_failures": 0,
            "elapsed_seconds": round(time.time() - start_ts, 2),
        }

    # ── 5. Region polygon filter (Punjab + Haryana boundary) ─────────────
    region_geojson_path = (
        Path(__file__).resolve().parent.parent.parent / "data" / "region.geojson"
    )
    try:
        region_boundary = load_region_boundary(region_geojson_path)
    except Exception as exc:
        _log("ERROR", "Failed to load region.geojson", error=str(exc))
        raise RuntimeError(f"Region boundary load failed: {exc}") from exc

    in_region = [
        d for d in detections
        if is_point_in_geojson(d["lat"], d["lon"], region_boundary)
    ]
    _log("INFO", "Region filter complete", in_region=len(in_region), total=len(detections))

    if not in_region:
        _log("WARN", "No detections inside Punjab/Haryana boundary")
        return {
            "day": ist_day,
            "clusters_written": 0,
            "impact_written": 0,
            "alerts_sent": 0,
            "partial_failures": 0,
            "elapsed_seconds": round(time.time() - start_ts, 2),
        }

    # ── 6. Cluster ────────────────────────────────────────────────────────
    clusters = cluster_detections(in_region)
    _log("INFO", "Clustering complete", clusters=len(clusters))

    # ── 7. Wind assignment ────────────────────────────────────────────────
    grid_points = build_wind_grid(
        min_lat=REGION_MIN_LAT,
        max_lat=REGION_MAX_LAT,
        min_lon=REGION_MIN_LON,
        max_lon=REGION_MAX_LON,
    )
    try:
        wind_data = fetch_wind_data(grid_points=grid_points, date=firms_date)
        grid_wind_map = parse_wind_forecast(wind_data)
        clusters_with_wind = [assign_wind_to_cluster(c, grid_wind_map) for c in clusters]
    except Exception as exc:
        _log("ERROR", "Wind data fetch/assignment failed", error=str(exc))
        raise RuntimeError(f"Wind pipeline failed: {exc}") from exc

    _log("INFO", "Wind data assigned", clusters_with_wind=len(clusters_with_wind))

    # ── 8. Load cities and compute impact ─────────────────────────────────
    cities_path = (
        Path(__file__).resolve().parent.parent.parent / "data" / "cities.json"
    )
    try:
        with open(cities_path, encoding="utf-8") as fh:
            cities: list[dict[str, Any]] = json.load(fh)
    except Exception as exc:
        _log("ERROR", "Failed to load cities.json", error=str(exc))
        raise RuntimeError(f"Cities data load failed: {exc}") from exc

    impact_records = compute_impact(clusters_with_wind, cities)
    _log("INFO", "Impact computed", cities_affected=len(impact_records))

    # ── 9. DynamoDB writes (idempotent) ───────────────────────────────────
    partial_failures = 0

    c_written, c_failed = _write_clusters(clusters_with_wind, ist_day, clusters_table)
    partial_failures += c_failed
    _log("INFO", "Clusters written", written=c_written, failed=c_failed)

    i_written, i_failed = _write_impact(impact_records, ist_day, impact_table)
    partial_failures += i_failed
    _log("INFO", "Impact records written", written=i_written, failed=i_failed)

    # ── 10. SNS alerts (High severity only, conditional update cooldown check)
    alerts_sent = 0
    now_utc_iso = datetime.now(tz=timezone.utc).isoformat()
    for record in impact_records:
        city_id = record["cityId"]
        severity = record.get("severity", "Low")
        if severity == "High":
            if _attempt_claim_alert(city_id, ist_day, impact_table, now_utc_iso):
                _publish_city_alert(
                    city_id=city_id,
                    city_name=record.get("cityName", city_id),
                    severity=severity,
                    ist_day=ist_day,
                    n_clusters=record.get("nClusters", 0),
                    total_frp=float(record.get("totalFrp", 0.0)),
                    nearest_km=float(record.get("nearestKm", 0.0)),
                    min_eta_hours=float(record.get("minEtaHours", 0.0)),
                    account_id=aws_account_id,
                    region=aws_region,
                )
                alerts_sent += 1

    elapsed = round(time.time() - start_ts, 2)
    summary = {
        "day": ist_day,
        "clusters_written": c_written,
        "impact_written": i_written,
        "alerts_sent": alerts_sent,
        "partial_failures": partial_failures,
        "elapsed_seconds": elapsed,
    }
    _log("INFO", "Ingest Lambda complete", **summary)

    if partial_failures > 0:
        _log(
            "WARN",
            f"Ingest completed with {partial_failures} partial DynamoDB failure(s)",
            partial_failures=partial_failures,
        )

    return summary
