"""Tests for backend/src/handlers/api.py (T-033).

Mock declarations (all labelled [MOCK] inline):
  - DynamoDB resource: [MOCK] injected directly into api._dynamo_resource;
                       no AWS credentials or network calls needed.
  - boto3:             boto3 is only present in the Lambda runtime, not in local dev env;
                       lazy import and global injection bypass boto3 import.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.handlers.api as api

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------
SAMPLE_CLUSTER_ITEMS = [
    {
        "day": "2024-11-01",
        "clusterId": "30.8500_75.2500",
        "lat": "30.8542",
        "lon": "75.2481",
        "count": 12,
        "totalFrp": "345.6",
        "maxFrp": "98.2",
        "firstSeenUtc": "2024-11-01T06:30:00Z",
        "lastSeenUtc": "2024-11-01T08:15:00Z",
        "windSpeedKmh": "18.5",
        "windDirDeg": "310.0",
        "ttl": 1792322345,
    },
    {
        "day": "2024-11-01",
        "clusterId": "31.2000_75.6000",
        "lat": "31.2011",
        "lon": "75.5982",
        "count": 5,
        "totalFrp": "120.4",
        "maxFrp": "50.1",
        "firstSeenUtc": "2024-11-01T07:00:00Z",
        "lastSeenUtc": "2024-11-01T09:30:00Z",
        "windSpeedKmh": "15.0",
        "windDirDeg": "305.0",
        "ttl": 1792322345,
    },
]

SAMPLE_IMPACT_ITEMS = [
    {
        "day": "2024-11-01",
        "cityId": "ludhiana",
        "cityName": "Ludhiana",
        "nClusters": 34,
        "totalFrp": "1250.4",
        "nearestKm": "18.2",
        "minEtaHours": "1.2",
        "severity": "High",
        "affectedByClusterIds": ["30.8500_75.2500"],
        "ttl": 1792322352,
    },
    {
        "day": "2024-11-01",
        "cityId": "ambala",
        "cityName": "Ambala",
        "nClusters": 10,
        "totalFrp": "314.8",
        "nearestKm": "42.0",
        "minEtaHours": "2.8",
        "severity": "Medium",
        "affectedByClusterIds": ["31.2000_75.6000"],
        "ttl": 1792322352,
    },
    {
        "day": "2024-11-01",
        "cityId": "delhi",
        "cityName": "Delhi",
        "nClusters": 3,
        "totalFrp": "55.0",
        "nearestKm": "120.5",
        "minEtaHours": "8.5",
        "severity": "Low",
        "affectedByClusterIds": [],
        "ttl": 1792322352,
    },
]


@pytest.fixture(autouse=True)
def reset_api_globals(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset module-level caches before each test."""
    monkeypatch.setattr(api, "_dynamo_resource", None)
    monkeypatch.setattr(api, "_cached_cities", None)


def _make_mock_dynamo(items: list[dict[str, Any]]) -> MagicMock:
    """Create a mock DynamoDB resource returning given items."""
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": items}
    mock_resource.Table.return_value = mock_table
    return mock_resource


# ---------------------------------------------------------------------------
# GET /cities tests
# ---------------------------------------------------------------------------
class TestGetCities:
    def test_cities_success(self) -> None:
        event = {
            "rawPath": "/cities",
            "requestContext": {"http": {"method": "GET", "path": "/cities"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        assert "public, max-age=300" in res["headers"]["Cache-Control"]
        assert res["headers"]["Access-Control-Allow-Origin"] == "*"

        body = json.loads(res["body"])
        assert "cities" in body
        assert body["total"] == 15
        assert len(body["cities"]) == 15
        # Verify schema of first city
        first = body["cities"][0]
        assert "id" in first
        assert "name" in first
        assert "lat" in first
        assert "lon" in first

    def test_cities_with_stage_prefix(self) -> None:
        event = {
            "rawPath": "/prod/cities",
            "requestContext": {
                "stage": "prod",
                "http": {"method": "GET", "path": "/prod/cities"},
            },
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        assert body["total"] == 15


# ---------------------------------------------------------------------------
# GET /clusters tests
# ---------------------------------------------------------------------------
class TestGetClusters:
    def test_clusters_valid_day(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_dynamo = _make_mock_dynamo(SAMPLE_CLUSTER_ITEMS)
        monkeypatch.setattr(api, "_dynamo_resource", mock_dynamo)

        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"day": "2024-11-01"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        assert "public, max-age=60" in res["headers"]["Cache-Control"]

        body = json.loads(res["body"])
        assert body["day"] == "2024-11-01"
        assert len(body["clusters"]) == 2

        # Verify computed stats
        stats = body["stats"]
        assert stats["totalClusters"] == 2
        assert stats["totalFires"] == 17
        assert stats["totalFrp"] == 466.0
        assert stats["maxFrp"] == 98.2
        assert stats["avgWindSpeedKmh"] == 16.8
        assert body["lastUpdatedUtc"] == "2024-11-01T09:30:00Z"

    def test_clusters_valid_window(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_dynamo = _make_mock_dynamo(SAMPLE_CLUSTER_ITEMS)
        monkeypatch.setattr(api, "_dynamo_resource", mock_dynamo)

        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"window": "24h"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        assert "clusters" in body
        assert "stats" in body

    def test_clusters_empty_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_dynamo = _make_mock_dynamo([])
        monkeypatch.setattr(api, "_dynamo_resource", mock_dynamo)

        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"day": "2026-10-11"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200

        body = json.loads(res["body"])
        assert body["clusters"] == []
        assert body["stats"]["totalClusters"] == 0
        assert body["stats"]["totalFires"] == 0
        assert body["stats"]["totalFrp"] == 0.0
        assert body["stats"]["maxFrp"] == 0.0
        assert body["stats"]["avgWindSpeedKmh"] == 0.0
        assert body["lastUpdatedUtc"] is None

    def test_clusters_invalid_day_format(self) -> None:
        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"day": "invalid-date"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
        assert "Invalid date format" in body["error"]["message"]

    def test_clusters_invalid_calendar_date(self) -> None:
        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"day": "2024-02-31"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    def test_clusters_invalid_window_format(self) -> None:
        event = {
            "rawPath": "/clusters",
            "queryStringParameters": {"window": "9999h"},
            "requestContext": {"http": {"method": "GET", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
        assert "cannot exceed 168h" in body["error"]["message"]


# ---------------------------------------------------------------------------
# GET /impact tests
# ---------------------------------------------------------------------------
class TestGetImpact:
    def test_impact_valid_day(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_dynamo = _make_mock_dynamo(SAMPLE_IMPACT_ITEMS)
        monkeypatch.setattr(api, "_dynamo_resource", mock_dynamo)

        event = {
            "rawPath": "/impact",
            "queryStringParameters": {"day": "2024-11-01"},
            "requestContext": {"http": {"method": "GET", "path": "/impact"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        assert "public, max-age=60" in res["headers"]["Cache-Control"]

        body = json.loads(res["body"])
        assert body["day"] == "2024-11-01"
        assert len(body["impact"]) == 3

        # Verify sorted descending by totalFrp
        assert body["impact"][0]["cityId"] == "ludhiana"
        assert body["impact"][0]["totalFrp"] == 1250.4
        assert body["impact"][1]["cityId"] == "ambala"
        assert body["impact"][2]["cityId"] == "delhi"

        # Verify computed stats
        stats = body["stats"]
        assert stats["totalCitiesAffected"] == 3
        assert stats["highSeverityCount"] == 1
        assert stats["mediumSeverityCount"] == 1
        assert stats["lowSeverityCount"] == 1
        assert stats["maxCityFrp"] == 1250.4
        assert body["lastUpdatedUtc"] is not None

    def test_impact_empty_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_dynamo = _make_mock_dynamo([])
        monkeypatch.setattr(api, "_dynamo_resource", mock_dynamo)

        event = {
            "rawPath": "/impact",
            "queryStringParameters": {"day": "2026-10-11"},
            "requestContext": {"http": {"method": "GET", "path": "/impact"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200

        body = json.loads(res["body"])
        assert body["impact"] == []
        assert body["stats"]["totalCitiesAffected"] == 0
        assert body["stats"]["highSeverityCount"] == 0
        assert body["stats"]["mediumSeverityCount"] == 0
        assert body["stats"]["lowSeverityCount"] == 0
        assert body["stats"]["maxCityFrp"] == 0.0
        assert body["lastUpdatedUtc"] is None

    def test_impact_invalid_params(self) -> None:
        event = {
            "rawPath": "/impact",
            "queryStringParameters": {"day": "bad-date"},
            "requestContext": {"http": {"method": "GET", "path": "/impact"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"


# ---------------------------------------------------------------------------
# Routing, Methods, Errors & CORS
# ---------------------------------------------------------------------------
class TestRoutingAndErrors:
    def test_root_endpoint(self) -> None:
        event = {
            "rawPath": "/",
            "requestContext": {"http": {"method": "GET", "path": "/"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        assert body["service"] == "DownWind API"
        assert "/cities" in body["endpoints"]

    def test_not_found(self) -> None:
        event = {
            "rawPath": "/nonexistent",
            "requestContext": {"http": {"method": "GET", "path": "/nonexistent"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 404
        body = json.loads(res["body"])
        assert body["error"]["code"] == "NOT_FOUND"

    def test_method_not_allowed(self) -> None:
        event = {
            "rawPath": "/cities",
            "requestContext": {"http": {"method": "POST", "path": "/cities"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 405
        body = json.loads(res["body"])
        assert body["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_cors_preflight(self) -> None:
        event = {
            "rawPath": "/clusters",
            "requestContext": {"http": {"method": "OPTIONS", "path": "/clusters"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 204
        assert res["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET" in res["headers"]["Access-Control-Allow-Methods"]
        assert "POST" in res["headers"]["Access-Control-Allow-Methods"]


# ---------------------------------------------------------------------------
# POST /subscribe Endpoint Tests (T-036)
# ---------------------------------------------------------------------------
class TestSubscribeEndpoint:
    @pytest.fixture(autouse=True)
    def setup_sns_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """[MOCK] Injected mock SNS client for isolated unit testing.

        Sets CITY_TOPIC_PREFIX matching the SAM Globals pattern.
        In production SAM always injects CITY_TOPIC_PREFIX; tests must mirror
        that so the security fix (no hardcoded account ID fallback) works.
        """
        monkeypatch.setenv(
            "CITY_TOPIC_PREFIX",
            "arn:aws:sns:ap-south-1:123456789012:downwind-city-",
        )
        monkeypatch.setenv("ENVIRONMENT", "prod")
        self.mock_sns = MagicMock()
        self.mock_sns.subscribe.return_value = {
            "SubscriptionArn": "pending confirmation"
        }
        api.set_sns_client(self.mock_sns)

    def test_subscribe_success(self) -> None:
        """Valid subscription returns 202 Accepted and calls SNS Subscribe."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps({"email": "User.Name+Test@Example.Com", "cityId": "Delhi"}),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 202
        body = json.loads(res["body"])
        assert body["status"] == "accepted"
        assert body["cityId"] == "delhi"
        assert "confirmation link" in body["message"]

        # Verify SNS subscribe was invoked with normalized email and correct topic ARN
        self.mock_sns.subscribe.assert_called_once()
        call_kwargs = self.mock_sns.subscribe.call_args.kwargs
        assert call_kwargs["Protocol"] == "email"
        assert call_kwargs["Endpoint"] == "user.name+test@example.com"
        assert call_kwargs["TopicArn"].endswith("downwind-city-delhi-prod")
        assert res["headers"]["Cache-Control"] == "no-cache, no-store, must-revalidate"
        assert res["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_subscribe_uniform_response_duplicate(self) -> None:
        """Duplicate subscription returns the exact same 202 response (enumeration prevention)."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps({"email": "resident@delhi.gov.in", "cityId": "delhi"}),
        }
        res1 = api.lambda_handler(event, None)
        res2 = api.lambda_handler(event, None)
        assert res1["statusCode"] == 202
        assert res2["statusCode"] == 202
        assert json.loads(res1["body"]) == json.loads(res2["body"])

    def test_subscribe_missing_body(self) -> None:
        """Missing request body returns 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": None,
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    def test_subscribe_invalid_json(self) -> None:
        """Malformed JSON returns 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": "{malformed_json: true,",
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    def test_subscribe_body_not_dict(self) -> None:
        """JSON array instead of object returns 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps(["user@example.com", "delhi"]),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {"email": 12345, "cityId": "delhi"},
            {"email": "user@example.com", "cityId": 123},
            {"cityId": "delhi"},
            {"email": "user@example.com"},
            {"email": "", "cityId": "delhi"},
            {"email": "   ", "cityId": "delhi"},
        ],
    )
    def test_subscribe_invalid_fields(self, invalid_payload: dict[str, Any]) -> None:
        """Missing or non-string fields return 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps(invalid_payload),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    @pytest.mark.parametrize(
        "bad_email",
        [
            "not-an-email",
            "@missinguser.com",
            "user@.com",
            "user@domain..com",
            "user..name@domain.com",
            "user name@domain.com",
            "user@localhost",
            "user@" + "a" * 260 + ".com",
        ],
    )
    def test_subscribe_invalid_email_format(self, bad_email: str) -> None:
        """Invalid email formats return 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps({"email": bad_email, "cityId": "delhi"}),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
        assert "Invalid email address format" in body["error"]["message"]

    def test_subscribe_invalid_city_id(self) -> None:
        """CityId not in allow-list returns 400 Bad Request."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps({"email": "user@example.com", "cityId": "mumbai"}),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 400
        body = json.loads(res["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
        assert "Allowed cities" in body["error"]["message"]

    def test_subscribe_base64_encoded(self) -> None:
        """Base64-encoded body decodes properly."""
        import base64

        raw = json.dumps({"email": "b64user@example.com", "cityId": "gurugram"}).encode()
        b64 = base64.b64encode(raw).decode()
        event = {
            "rawPath": "/subscribe",
            "isBase64Encoded": True,
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": b64,
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 202
        body = json.loads(res["body"])
        assert body["cityId"] == "gurugram"

    def test_subscribe_method_not_allowed(self) -> None:
        """GET /subscribe returns 405 Method Not Allowed."""
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "GET", "path": "/subscribe"}},
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 405
        body = json.loads(res["body"])
        assert body["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_subscribe_sns_internal_error(self) -> None:
        """SNS client failure returns 500 Internal Error without leaking details."""
        self.mock_sns.subscribe.side_effect = RuntimeError("SNS throttled or unreachable")
        event = {
            "rawPath": "/subscribe",
            "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
            "body": json.dumps({"email": "user@example.com", "cityId": "chandigarh"}),
        }
        res = api.lambda_handler(event, None)
        assert res["statusCode"] == 500
        body = json.loads(res["body"])
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_subscribe_all_15_cities(self) -> None:
        """All 15 starter cities can be subscribed successfully."""
        cities = api.get_allowed_city_ids()
        assert len(cities) == 15
        for city_id in cities:
            self.mock_sns.reset_mock()
            event = {
                "rawPath": "/subscribe",
                "requestContext": {"http": {"method": "POST", "path": "/subscribe"}},
                "body": json.dumps({"email": "all@example.com", "cityId": city_id}),
            }
            res = api.lambda_handler(event, None)
            assert res["statusCode"] == 202
            call_kwargs = self.mock_sns.subscribe.call_args.kwargs
            assert call_kwargs["TopicArn"].endswith(f"downwind-city-{city_id}-prod")

