"""API Lambda handler for DownWind (T-033).

Responsibility:
  Serves HTTP API read endpoints consumed by the frontend and external clients:
    - GET /cities   — returns the starter cities list from static backend/data/cities.json
    - GET /clusters — returns fire clusters with computed stats and lastUpdatedUtc
    - GET /impact   — returns city-level smoke impact records with computed stats

Query parameter contract:
  - ?day=YYYY-MM-DD: query a specific IST calendar date
  - ?window=24h|48h|...: query rolling time horizon
    (defaults to 24h if neither day nor window provided)
  - Standard error shape: {"error": {"code": "...", "message": "..."}}
  - Short cache headers for fast client/CDN responses.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IST_TIMEZONE: timezone = timezone(timedelta(hours=5, minutes=30))
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WINDOW_REGEX = re.compile(r"^(\d+)(h|d)$")
# RFC 5322 compliant practical email pattern
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# Cache headers
CACHE_CITIES_HEADER = "public, max-age=300, s-maxage=300"
CACHE_DYNAMIC_HEADER = "public, max-age=60, s-maxage=60"
CACHE_NO_STORE_HEADER = "no-cache, no-store, must-revalidate"

# Module-level caches
_dynamo_resource: Any = None
_sns_client: Any = None
_cached_cities: list[dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# AWS SDK factories (lazy import per D-024)
# ---------------------------------------------------------------------------
def _get_dynamo_resource() -> Any:
    global _dynamo_resource
    if _dynamo_resource is None:
        import boto3  # noqa: PLC0415 — lazy import for Lambda runtime only
        _dynamo_resource = boto3.resource("dynamodb")
    return _dynamo_resource


def set_dynamo_resource(resource: Any) -> None:
    """Set custom or mock DynamoDB resource for testing."""
    global _dynamo_resource
    _dynamo_resource = resource


def _get_sns_client() -> Any:
    global _sns_client
    if _sns_client is None:
        import boto3  # noqa: PLC0415 — lazy import for Lambda runtime only
        _sns_client = boto3.client("sns")
    return _sns_client


def set_sns_client(client: Any) -> None:
    """Set custom or mock SNS client for testing."""
    global _sns_client
    _sns_client = client


# ---------------------------------------------------------------------------
# HTTP Response Helpers
# ---------------------------------------------------------------------------
def _json_response(
    status_code: int,
    body: dict[str, Any],
    cache_control: str = CACHE_DYNAMIC_HEADER,
) -> dict[str, Any]:
    """Build a standard HTTP API Gateway 2.0 response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Cache-Control": cache_control,
        },
        "body": json.dumps(body),
    }


def _error_response(status_code: int, code: str, message: str) -> dict[str, Any]:
    """Build a standard error response matching architecture.md §5."""
    return _json_response(
        status_code=status_code,
        body={"error": {"code": code, "message": message}},
        cache_control=CACHE_NO_STORE_HEADER,
    )


# ---------------------------------------------------------------------------
# Query parameter validation
# ---------------------------------------------------------------------------
def _parse_and_validate_query(
    query_params: dict[str, str] | None,
) -> tuple[str | None, list[str], str]:
    """Parse and validate query parameters.

    Returns:
        tuple of (error_message, target_days_list, primary_day_string).
        If validation fails, error_message is non-empty.
    """
    params = query_params or {}

    # 1. Explicit day query
    if "day" in params:
        day_str = params["day"].strip()
        if not DATE_REGEX.match(day_str):
            return (
                "Invalid date format for 'day'. Expected YYYY-MM-DD (e.g. 2024-11-01).",
                [],
                "",
            )
        try:
            parsed_dt = datetime.strptime(day_str, "%Y-%m-%d")
            # Sanity range check (2020 to 2035)
            if not (2020 <= parsed_dt.year <= 2035):
                return ("Date out of supported range (2020-2035).", [], "")
        except ValueError:
            return ("Invalid calendar date provided for 'day'.", [], "")

        return (None, [day_str], day_str)

    # 2. Window query
    if "window" in params:
        window_str = params["window"].strip().lower()
        match = WINDOW_REGEX.match(window_str)
        if not match:
            return (
                "Invalid format for 'window'. Expected e.g. '24h', '48h', or '7d'.",
                [],
                "",
            )

        value = int(match.group(1))
        unit = match.group(2)
        hours = value * 24 if unit == "d" else value

        if hours <= 0:
            return ("'window' must be greater than 0.", [], "")
        if hours > 168:
            return ("'window' cannot exceed 168h (7 days).", [], "")

        now_ist = datetime.now(tz=IST_TIMEZONE)
        primary_day = now_ist.strftime("%Y-%m-%d")

        # Collect distinct IST dates spanned by this window
        start_dt = now_ist - timedelta(hours=hours)
        days: list[str] = []
        cur_dt = start_dt
        while cur_dt.date() <= now_ist.date():
            days.append(cur_dt.strftime("%Y-%m-%d"))
            cur_dt += timedelta(days=1)

        return (None, days, primary_day)

    # 3. Default: current IST date
    today_str = datetime.now(tz=IST_TIMEZONE).strftime("%Y-%m-%d")
    return (None, [today_str], today_str)


# ---------------------------------------------------------------------------
# Data Loaders & Normalizers
# ---------------------------------------------------------------------------
def _load_cities() -> list[dict[str, Any]]:
    """Load and cache the starter cities list from backend/data/cities.json."""
    global _cached_cities
    if _cached_cities is not None:
        return _cached_cities

    cities_path = (
        Path(__file__).resolve().parent.parent.parent / "data" / "cities.json"
    )
    with open(cities_path, encoding="utf-8") as fh:
        _cached_cities = json.load(fh)

    assert _cached_cities is not None
    return _cached_cities


def _query_dynamo_by_day(table_name: str, day: str) -> list[dict[str, Any]]:
    """Query a DynamoDB table for a specific IST date partition key."""
    dynamo = _get_dynamo_resource()
    table = dynamo.Table(table_name)

    items: list[dict[str, Any]] = []
    response = table.query(
        KeyConditionExpression="#d = :day",
        ExpressionAttributeNames={"#d": "day"},
        ExpressionAttributeValues={":day": day},
    )
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.query(
            KeyConditionExpression="#d = :day",
            ExpressionAttributeNames={"#d": "day"},
            ExpressionAttributeValues={":day": day},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    return items


def _normalize_cluster(item: dict[str, Any]) -> dict[str, Any]:
    """Convert DynamoDB cluster item attributes to typed values."""
    return {
        "clusterId": str(item.get("clusterId", "")),
        "lat": round(float(item.get("lat", 0.0)), 4),
        "lon": round(float(item.get("lon", 0.0)), 4),
        "count": int(item.get("count", 0)),
        "totalFrp": round(float(item.get("totalFrp", 0.0)), 1),
        "maxFrp": round(float(item.get("maxFrp", 0.0)), 1),
        "firstSeenUtc": str(item.get("firstSeenUtc", "")),
        "lastSeenUtc": str(item.get("lastSeenUtc", "")),
        "windSpeedKmh": round(float(item.get("windSpeedKmh", 0.0)), 1),
        "windDirDeg": round(float(item.get("windDirDeg", 0.0)), 1),
    }


def _normalize_impact(item: dict[str, Any]) -> dict[str, Any]:
    """Convert DynamoDB impact item attributes to typed values."""
    return {
        "cityId": str(item.get("cityId", "")),
        "cityName": str(item.get("cityName", "")),
        "nClusters": int(item.get("nClusters", 0)),
        "totalFrp": round(float(item.get("totalFrp", 0.0)), 1),
        "nearestKm": round(float(item.get("nearestKm", 0.0)), 1),
        "minEtaHours": round(float(item.get("minEtaHours", 0.0)), 1),
        "severity": str(item.get("severity", "Low")),
        "affectedByClusterIds": list(item.get("affectedByClusterIds", [])),
    }


# ---------------------------------------------------------------------------
# Endpoint Handlers
# ---------------------------------------------------------------------------
def handle_cities() -> dict[str, Any]:
    """GET /cities — returns starter cities list."""
    try:
        cities = _load_cities()
        return _json_response(
            200,
            {"cities": cities, "total": len(cities)},
            cache_control=CACHE_CITIES_HEADER,
        )
    except Exception as exc:
        return _error_response(
            500, "INTERNAL_ERROR", f"Failed to load cities: {exc}"
        )


def handle_clusters(query_params: dict[str, str] | None) -> dict[str, Any]:
    """GET /clusters — returns clusters with computed stats and lastUpdatedUtc."""
    err, days, primary_day = _parse_and_validate_query(query_params)
    if err:
        return _error_response(400, "BAD_REQUEST", err)

    table_name = os.environ.get("CLUSTERS_TABLE", "downwind-clusters-prod")

    try:
        all_items: list[dict[str, Any]] = []
        for day in days:
            all_items.extend(_query_dynamo_by_day(table_name, day))

        # Deduplicate by clusterId if multiple days spanned
        seen_cluster_ids: set[str] = set()
        clusters: list[dict[str, Any]] = []
        for raw in all_items:
            cid = str(raw.get("clusterId", ""))
            if cid and cid not in seen_cluster_ids:
                seen_cluster_ids.add(cid)
                clusters.append(_normalize_cluster(raw))

        # Compute summary stats
        total_clusters = len(clusters)
        total_fires = sum(c["count"] for c in clusters)
        total_frp = round(sum(c["totalFrp"] for c in clusters), 1)
        max_frp = (
            round(max(c["maxFrp"] for c in clusters), 1)
            if clusters
            else 0.0
        )
        avg_wind_speed = (
            round(sum(c["windSpeedKmh"] for c in clusters) / total_clusters, 1)
            if total_clusters > 0
            else 0.0
        )

        last_updated: str | None = None
        seen_dates = [c["lastSeenUtc"] for c in clusters if c["lastSeenUtc"]]
        if seen_dates:
            last_updated = max(seen_dates)

        stats = {
            "totalClusters": total_clusters,
            "totalFires": total_fires,
            "totalFrp": total_frp,
            "maxFrp": max_frp,
            "avgWindSpeedKmh": avg_wind_speed,
        }

        return _json_response(
            200,
            {
                "day": primary_day,
                "clusters": clusters,
                "stats": stats,
                "lastUpdatedUtc": last_updated,
            },
        )
    except Exception as exc:
        return _error_response(
            500, "INTERNAL_ERROR", f"Failed to retrieve clusters: {exc}"
        )


def handle_impact(query_params: dict[str, str] | None) -> dict[str, Any]:
    """GET /impact — returns city-wise smoke impact with computed stats."""
    err, days, primary_day = _parse_and_validate_query(query_params)
    if err:
        return _error_response(400, "BAD_REQUEST", err)

    table_name = os.environ.get("IMPACT_TABLE", "downwind-impact-prod")

    try:
        all_items: list[dict[str, Any]] = []
        for day in days:
            all_items.extend(_query_dynamo_by_day(table_name, day))

        # Deduplicate by cityId if multiple days spanned
        seen_city_ids: set[str] = set()
        impacts: list[dict[str, Any]] = []
        for raw in all_items:
            cid = str(raw.get("cityId", ""))
            if cid and cid not in seen_city_ids:
                seen_city_ids.add(cid)
                impacts.append(_normalize_impact(raw))

        # Sort by totalFrp descending (highest impact first)
        impacts.sort(key=lambda x: x["totalFrp"], reverse=True)

        total_affected = len(impacts)
        high_count = sum(1 for i in impacts if i["severity"] == "High")
        med_count = sum(1 for i in impacts if i["severity"] == "Medium")
        low_count = sum(1 for i in impacts if i["severity"] == "Low")
        max_city_frp = (
            round(max(i["totalFrp"] for i in impacts), 1)
            if impacts
            else 0.0
        )

        stats = {
            "totalCitiesAffected": total_affected,
            "highSeverityCount": high_count,
            "mediumSeverityCount": med_count,
            "lowSeverityCount": low_count,
            "maxCityFrp": max_city_frp,
        }

        # Resolve lastUpdatedUtc from current timestamp or record TTL
        last_updated: str | None = None
        if impacts:
            last_updated = datetime.now(tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return _json_response(
            200,
            {
                "day": primary_day,
                "impact": impacts,
                "stats": stats,
                "lastUpdatedUtc": last_updated,
            },
        )
    except Exception as exc:
        return _error_response(
            500, "INTERNAL_ERROR", f"Failed to retrieve impact: {exc}"
        )


# ---------------------------------------------------------------------------
# Top-level Lambda Handler
# ---------------------------------------------------------------------------
# POST /subscribe Validation & Handler (T-036)
# ---------------------------------------------------------------------------
def validate_email_address(email: str) -> bool:
    """Validate email address format strictly per RFC 5322 rules.

    Checks:
      - Total length <= 254 chars (RFC 5321 limit)
      - Exactly one '@' separating local and domain
      - Local part 1..64 chars, domain part 1..253 chars
      - No leading/trailing/consecutive dots in local or domain
      - Domain contains at least one dot
      - Matches EMAIL_REGEX
    """
    if not email or len(email) > 254:
        return False
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local_part, domain_part = parts
    if not local_part or len(local_part) > 64:
        return False
    if not domain_part or len(domain_part) > 253:
        return False
    if ".." in email:
        return False
    if local_part.startswith(".") or local_part.endswith("."):
        return False
    if domain_part.startswith(".") or domain_part.endswith("."):
        return False
    if "." not in domain_part:
        return False
    return bool(EMAIL_REGEX.match(email))


def get_allowed_city_ids() -> set[str]:
    """Return set of valid city IDs from the configured starter cities."""
    cities = _load_cities()
    return {c["id"].lower() for c in cities if "id" in c}


def get_city_topic_arn(city_id: str) -> str:
    """Derive the SNS topic ARN for a given city ID.

    Format: {CITY_TOPIC_PREFIX}{city_id}-{ENVIRONMENT}
    Matches the naming in template.yaml: downwind-city-{city_id}-{env}.
    """
    env = os.environ.get("ENVIRONMENT", "prod")
    prefix = os.environ.get("CITY_TOPIC_PREFIX")
    if prefix:
        return f"{prefix}{city_id}-{env}"

    region = os.environ.get("AWS_REGION", "ap-south-1")
    account_id = os.environ.get("AWS_ACCOUNT_ID", "694442891430")
    return f"arn:aws:sns:{region}:{account_id}:downwind-city-{city_id}-{env}"


def handle_subscribe(event: dict[str, Any]) -> dict[str, Any]:
    """Handle POST /subscribe requests per architecture.md §5 and T-036.

    Contract:
      - Payload: {"email": "...", "cityId": "..."}
      - Validates body is a non-empty JSON object
      - Validates email format strictly
      - Validates cityId against the starter 15 cities allow-list
      - Initiates SNS email double opt-in subscription
      - Returns uniform HTTP 202 Accepted response for all valid inputs
        to prevent email enumeration.
    """
    body_raw = event.get("body")
    if not body_raw:
        return _error_response(400, "BAD_REQUEST", "Request body is required.")

    if event.get("isBase64Encoded"):
        import base64

        try:
            body_raw = base64.b64decode(body_raw).decode("utf-8")
        except Exception:
            return _error_response(
                400, "BAD_REQUEST", "Failed to decode base64 request body."
            )

    try:
        data = json.loads(body_raw)
    except (json.JSONDecodeError, TypeError):
        return _error_response(400, "BAD_REQUEST", "Invalid JSON in request body.")

    if not isinstance(data, dict):
        return _error_response(
            400, "BAD_REQUEST", "Request body must be a JSON object."
        )

    email_raw = data.get("email")
    city_id_raw = data.get("cityId")

    if not isinstance(email_raw, str) or not isinstance(city_id_raw, str):
        return _error_response(
            400, "BAD_REQUEST", "Fields 'email' and 'cityId' must be strings."
        )

    email = email_raw.strip().lower()
    city_id = city_id_raw.strip().lower()

    if not email:
        return _error_response(400, "BAD_REQUEST", "Field 'email' cannot be empty.")

    if not validate_email_address(email):
        return _error_response(400, "BAD_REQUEST", "Invalid email address format.")

    allowed_cities = get_allowed_city_ids()
    if city_id not in allowed_cities:
        allowed_sorted = ", ".join(sorted(allowed_cities))
        return _error_response(
            400,
            "BAD_REQUEST",
            f"Invalid cityId '{city_id}'. Allowed cities: {allowed_sorted}.",
        )

    topic_arn = get_city_topic_arn(city_id)

    # Call SNS subscribe
    try:
        sns = _get_sns_client()
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
            ReturnSubscriptionArn=True,
        )
    except Exception as exc:
        masked_email = (
            email[:2] + "***@" + email.split("@")[-1] if "@" in email else "***"
        )
        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "message": "Failed to subscribe email to SNS topic",
                    "cityId": city_id,
                    "topicArn": topic_arn,
                    "maskedEmail": masked_email,
                    "error": str(exc),
                }
            )
        )
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "An error occurred while processing the subscription. Please try again later.",
        )

    # Uniform 202 Accepted response for all valid inputs (prevents email enumeration)
    return _json_response(
        status_code=202,
        body={
            "status": "accepted",
            "message": (
                "If the email address is valid, a confirmation link has been sent. "
                "Please check your inbox (and spam folder) to confirm subscription."
            ),
            "cityId": city_id,
        },
        cache_control=CACHE_NO_STORE_HEADER,
    )


# ---------------------------------------------------------------------------
# Top-level Lambda handler
# ---------------------------------------------------------------------------
def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """API Gateway HTTP API top-level entry point."""
    # 1. Resolve HTTP method
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "GET")
        .upper()
    )

    # 2. CORS preflight
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Cache-Control": CACHE_CITIES_HEADER,
            },
            "body": "",
        }

    # 3. Path resolution & stage prefix normalization
    raw_path = (
        event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or "/"
    )
    stage = event.get("requestContext", {}).get("stage")

    path = raw_path
    if stage and path.startswith(f"/{stage}/"):
        path = path[len(stage) + 1 :]
    elif stage and path == f"/{stage}":
        path = "/"
    elif path.startswith("/prod/"):
        path = path[5:]
    elif path == "/prod":
        path = "/"

    clean_path = path.rstrip("/") if path != "/" else "/"
    query_params: dict[str, str] = event.get("queryStringParameters") or {}

    # 4. Route dispatch
    if clean_path == "/subscribe":
        if method == "POST":
            return handle_subscribe(event)
        return _error_response(
            405, "METHOD_NOT_ALLOWED", f"HTTP method '{method}' is not allowed for /subscribe."
        )

    if clean_path in ("/cities", "/clusters", "/impact", "/"):
        if method != "GET":
            return _error_response(
                405, "METHOD_NOT_ALLOWED", f"HTTP method '{method}' is not allowed."
            )
        if clean_path == "/cities":
            return handle_cities()
        if clean_path == "/clusters":
            return handle_clusters(query_params)
        if clean_path == "/impact":
            return handle_impact(query_params)
        return _json_response(
            200,
            {
                "service": "DownWind API",
                "version": "1.0",
                "endpoints": ["/cities", "/clusters", "/impact", "/subscribe"],
            },
        )

    return _error_response(
        404, "NOT_FOUND", f"Route '{clean_path}' not found."
    )

