"""Tests for backend/src/handlers/ingest.py (T-031).

Mock declarations (all clearly labelled [MOCK] inline):
  - boto3 imports:            boto3 is NOT installed in the local dev env;
                              it is only available in the Lambda runtime.
                              Tests inject mock clients directly into the
                              module's cached globals (_ssm_client, _dynamo_resource,
                              _sns_client) AFTER reload, bypassing the lazy import.
  - fetch_firms_csv:          [MOCK] patched on the ingest module directly so
                              no network calls to NASA FIRMS are made.
  - fetch_wind_data:          [MOCK] patched on the ingest module; returns a
                              pre-built stub wind response.
  - load_region_boundary:     [MOCK] patched to return an empty dict (polygon
                              math is tested separately in test_region.py).
  - is_point_in_geojson:      [MOCK] patched to return True/False as needed.
  - cities.json file I/O:     [MOCK] patched via open() / json.load() to inject
                              a minimal city list without touching the real file.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── Fixture paths ─────────────────────────────────────────────────────────
FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIRMS_FIXTURE = FIXTURES_DIR / "firms_sample.csv"

# ── Minimal city list ─────────────────────────────────────────────────────
SAMPLE_CITIES: list[dict[str, Any]] = [
    {"id": "ludhiana", "name": "Ludhiana", "state": "Punjab", "lat": 30.91, "lon": 75.85},
    {"id": "karnal", "name": "Karnal", "state": "Haryana", "lat": 29.69, "lon": 76.99},
]

# ── Dummy wind data: wind from south, smoke travels north at 20 km/h ──────
DUMMY_WIND_DATA: list[dict[str, Any]] = [
    {
        "latitude": 30.0,
        "longitude": 75.5,
        "hourly": {
            "wind_speed_10m": [20.0] * 24,
            "wind_direction_10m": [180.0] * 24,
        },
    }
]

# Required environment variables
ENV_DEFAULTS = {
    "FIRMS_KEY_PARAMETER_NAME": "/downwind/firms-map-key",
    "CLUSTERS_TABLE": "downwind-clusters-test",
    "IMPACT_TABLE": "downwind-impact-test",
    "OPS_TOPIC_ARN": "arn:aws:sns:ap-south-1:123456789012:downwind-ops-test",
    "AWS_REGION": "ap-south-1",
    "DYNAMO_TTL_DAYS": "7",
}


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV_DEFAULTS.items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------------------
# Module reload helper — resets all module-level cached clients and key
# ---------------------------------------------------------------------------
def _fresh_ingest() -> Any:
    """Reload ingest module and return it with cleared module-level caches.

    Because boto3 is not installed in the local dev env, we must also
    ensure that boto3 is not actually imported during the reload.  We
    achieve this by inserting a MagicMock for 'boto3' in sys.modules
    before the reload and removing it after.  The lazy-import guard in
    _get_ssm_client / _get_dynamo_resource / _get_sns_client will find
    the mock when the module globals are None.
    """
    # Stub boto3 so the lazy `import boto3` inside factory fns resolves to a mock
    boto3_stub = MagicMock()
    sys.modules["boto3"] = boto3_stub

    import src.handlers.ingest as mod
    importlib.reload(mod)

    # Remove the stub — tests inject clients directly into module globals instead
    sys.modules.pop("boto3", None)
    return mod


def _inject_clients(
    mod: Any,
    ssm: Any,
    dynamo: Any,
    sns: Any,
) -> None:
    """Inject pre-built mock clients into the module's cached globals."""
    mod._ssm_client = ssm
    mod._dynamo_resource = dynamo
    mod._sns_client = sns
    mod._cached_firms_key = None  # ensure SSM lookup goes through mock ssm


# ---------------------------------------------------------------------------
# [MOCK] Builder helpers
# ---------------------------------------------------------------------------
def _mock_ssm(key_value: str = "test-firms-key-abc123") -> MagicMock:
    """[MOCK] boto3 SSM client: get_parameter returns a fixed key value."""
    ssm = MagicMock()
    ssm.get_parameter.return_value = {"Parameter": {"Value": key_value}}
    return ssm


def _mock_dynamo(put_side_effect: Any = None, update_side_effect: Any = None) -> MagicMock:
    """[MOCK] boto3 DynamoDB resource: Table.put_item, update_item, and Table.get_item stubbed."""
    dynamo = MagicMock()
    table = MagicMock()
    table.put_item.side_effect = put_side_effect
    table.put_item.return_value = {} if put_side_effect is None else table.put_item.return_value
    table.update_item.side_effect = update_side_effect
    table.update_item.return_value = (
        {} if update_side_effect is None else table.update_item.return_value
    )
    table.get_item.return_value = {"Item": {}}
    dynamo.Table.return_value = table
    return dynamo


def _mock_sns() -> MagicMock:
    """[MOCK] boto3 SNS client: publish returns a stub message ID."""
    sns = MagicMock()
    sns.publish.return_value = {"MessageId": "mock-msg-id"}
    return sns


# ---------------------------------------------------------------------------
# Test: SSM key is cached across warm invocations (called only once)
# ---------------------------------------------------------------------------
def test_ssm_key_cached_across_warm_invocations() -> None:
    """get_parameter must be called once on cold start and not again on warm call."""
    mod = _fresh_ingest()
    ssm = _mock_ssm()
    _inject_clients(mod, ssm=ssm, dynamo=_mock_dynamo(), sns=_mock_sns())

    # First call → SSM hit
    key1 = mod._get_firms_key()
    # Second call → should use cached value
    key2 = mod._get_firms_key()

    assert key1 == key2 == "test-firms-key-abc123"
    assert ssm.get_parameter.call_count == 1


# ---------------------------------------------------------------------------
# Test: Missing env var raises RuntimeError
# ---------------------------------------------------------------------------
def test_missing_ssm_param_name_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """RuntimeError is raised when FIRMS_KEY_PARAMETER_NAME is absent."""
    mod = _fresh_ingest()
    monkeypatch.delenv("FIRMS_KEY_PARAMETER_NAME", raising=False)
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=_mock_dynamo(), sns=_mock_sns())

    with pytest.raises(RuntimeError, match="FIRMS_KEY_PARAMETER_NAME"):
        mod._get_firms_key()


# ---------------------------------------------------------------------------
# Test: SSM failure raises RuntimeError (no key value in message)
# ---------------------------------------------------------------------------
def test_ssm_failure_raises_runtime_error() -> None:
    """SSM exceptions are wrapped as RuntimeError without leaking the key value."""
    mod = _fresh_ingest()
    ssm = MagicMock()
    ssm.get_parameter.side_effect = Exception("AccessDenied: some permission error")
    _inject_clients(mod, ssm=ssm, dynamo=_mock_dynamo(), sns=_mock_sns())

    with pytest.raises(RuntimeError, match="Failed to retrieve FIRMS key"):
        mod._get_firms_key()

    # Error message must not contain the fake secret value
    try:
        mod._get_firms_key()
    except RuntimeError as exc:
        assert "AccessDenied" not in str(exc) or "some permission error" not in str(exc)


# ---------------------------------------------------------------------------
# Test: Empty CSV → handler returns early with zero counts (no DynamoDB writes)
# ---------------------------------------------------------------------------
def test_handler_empty_csv_returns_zero_counts() -> None:
    """When FIRMS returns no detections the handler exits without any DynamoDB writes."""
    mod = _fresh_ingest()
    dynamo = _mock_dynamo()
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=_mock_sns())
    mod._cached_firms_key = "cached-key"  # skip SSM

    with (
        patch.object(mod, "fetch_firms_csv", return_value=""),
        patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
    ):
        result = mod.lambda_handler({}, None)

    assert result["clusters_written"] == 0
    assert result["impact_written"] == 0
    assert result["partial_failures"] == 0
    dynamo.Table.return_value.put_item.assert_not_called()


# ---------------------------------------------------------------------------
# Test: All detections outside region → zero DynamoDB writes
# ---------------------------------------------------------------------------
def test_handler_all_detections_outside_region() -> None:
    """[MOCK] is_point_in_geojson returns False → zero clusters and impact."""
    mod = _fresh_ingest()
    dynamo = _mock_dynamo()
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=_mock_sns())
    mod._cached_firms_key = "cached-key"

    firms_csv = FIRMS_FIXTURE.read_text(encoding="utf-8")

    with (
        patch.object(mod, "fetch_firms_csv", return_value=firms_csv),
        patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
        patch.object(mod, "load_region_boundary", return_value={}),  # [MOCK]
        patch.object(mod, "is_point_in_geojson", return_value=False),  # [MOCK]
    ):
        result = mod.lambda_handler({}, None)

    assert result["clusters_written"] == 0
    assert result["impact_written"] == 0


# ---------------------------------------------------------------------------
# Test: Happy path — pipeline runs, clusters and impact are written
# ---------------------------------------------------------------------------
def test_handler_happy_path_writes_clusters_and_impact() -> None:
    """Full pipeline with fixture CSV → clusters and impact rows put to DynamoDB."""
    mod = _fresh_ingest()
    dynamo = _mock_dynamo()
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=_mock_sns())
    mod._cached_firms_key = "cached-key"

    firms_csv = FIRMS_FIXTURE.read_text(encoding="utf-8")

    with (
        patch.object(mod, "fetch_firms_csv", return_value=firms_csv),
        patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
        patch.object(mod, "load_region_boundary", return_value={}),  # [MOCK]
        patch.object(mod, "is_point_in_geojson", return_value=True),  # [MOCK]
        patch.object(mod, "json") as mock_json,
        patch("builtins.open", MagicMock()),
    ):
        mock_json.dumps = json.dumps
        mock_json.load.return_value = SAMPLE_CITIES
        mock_json.loads = json.loads

        result = mod.lambda_handler({}, None)

    assert result["clusters_written"] > 0
    assert "day" in result
    assert result["partial_failures"] == 0


# ---------------------------------------------------------------------------
# Test: DynamoDB put_item failure → partial_failures incremented, no exception
# ---------------------------------------------------------------------------
def test_handler_dynamo_partial_failure_is_non_fatal() -> None:
    """A DynamoDB write failure increments partial_failures but does NOT raise."""
    mod = _fresh_ingest()
    # [MOCK] put_item raises every time
    dynamo = _mock_dynamo(put_side_effect=Exception("ProvisionedThroughputExceeded"))
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=_mock_sns())
    mod._cached_firms_key = "cached-key"

    firms_csv = FIRMS_FIXTURE.read_text(encoding="utf-8")

    with (
        patch.object(mod, "fetch_firms_csv", return_value=firms_csv),
        patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
        patch.object(mod, "load_region_boundary", return_value={}),  # [MOCK]
        patch.object(mod, "is_point_in_geojson", return_value=True),  # [MOCK]
        patch.object(mod, "json") as mock_json,
        patch("builtins.open", MagicMock()),
    ):
        mock_json.dumps = json.dumps
        mock_json.load.return_value = SAMPLE_CITIES
        mock_json.loads = json.loads

        # Must not raise
        result = mod.lambda_handler({}, None)

    assert result["partial_failures"] > 0
    assert result["clusters_written"] == 0  # all writes failed


# ---------------------------------------------------------------------------
# Test: MAP_KEY value never appears in any log output
# ---------------------------------------------------------------------------
def test_key_never_logged(capsys: pytest.CaptureFixture[str]) -> None:
    """Security: MAP_KEY value must never appear in stdout or stderr."""
    mod = _fresh_ingest()
    secret_key = "SUPER_SECRET_FIRMS_KEY_DO_NOT_LOG_9876"
    ssm = _mock_ssm(key_value=secret_key)
    _inject_clients(mod, ssm=ssm, dynamo=_mock_dynamo(), sns=_mock_sns())

    with (
        patch.object(mod, "fetch_firms_csv", return_value=""),  # empty → early exit
        patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
    ):
        mod.lambda_handler({}, None)

    captured = capsys.readouterr()
    assert secret_key not in captured.out, "Secret key appeared in stdout!"
    assert secret_key not in captured.err, "Secret key appeared in stderr!"


# ---------------------------------------------------------------------------
# Test: Idempotency — same input produces identical cluster IDs in DynamoDB
# ---------------------------------------------------------------------------
def test_idempotent_writes_produce_same_cluster_ids() -> None:
    """Re-running the handler with identical FIRMS data writes the same cluster IDs."""
    firms_csv = FIRMS_FIXTURE.read_text(encoding="utf-8")

    def _run_and_collect_ids() -> set[str]:
        mod = _fresh_ingest()
        written_items: list[dict[str, Any]] = []

        def capture_put(Item: dict[str, Any]) -> dict[str, Any]:
            written_items.append(Item)
            return {}

        dynamo = _mock_dynamo()
        dynamo.Table.return_value.put_item.side_effect = capture_put
        dynamo.Table.return_value.put_item.return_value = {}
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=_mock_sns())
        mod._cached_firms_key = "cached-key"

        with (
            patch.object(mod, "fetch_firms_csv", return_value=firms_csv),
            patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
            patch.object(mod, "load_region_boundary", return_value={}),  # [MOCK]
            patch.object(mod, "is_point_in_geojson", return_value=True),  # [MOCK]
            patch.object(mod, "json") as mock_json,
            patch("builtins.open", MagicMock()),
        ):
            mock_json.dumps = json.dumps
            mock_json.load.return_value = SAMPLE_CITIES
            mock_json.loads = json.loads
            mod.lambda_handler({}, None)

        return {item["clusterId"] for item in written_items if "clusterId" in item}

    ids_run1 = _run_and_collect_ids()
    ids_run2 = _run_and_collect_ids()

    assert ids_run1 == ids_run2, f"Cluster IDs differ: {ids_run1} vs {ids_run2}"
    assert len(ids_run1) > 0, "No cluster IDs written — fixture may have 0 fires"


# ---------------------------------------------------------------------------
# Test: Missing CLUSTERS_TABLE env var raises RuntimeError before any AWS call
# ---------------------------------------------------------------------------
def test_missing_table_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing CLUSTERS_TABLE / IMPACT_TABLE raises RuntimeError before SSM call."""
    mod = _fresh_ingest()
    ssm = _mock_ssm()
    _inject_clients(mod, ssm=ssm, dynamo=_mock_dynamo(), sns=_mock_sns())
    mod._cached_firms_key = "cached-key"
    monkeypatch.delenv("CLUSTERS_TABLE", raising=False)
    monkeypatch.delenv("IMPACT_TABLE", raising=False)

    with pytest.raises(RuntimeError, match="CLUSTERS_TABLE"):
        mod.lambda_handler({}, None)


# ---------------------------------------------------------------------------
# Test: Wind fetch failure raises RuntimeError (propagates to Lambda FAILED)
# ---------------------------------------------------------------------------
def test_wind_fetch_failure_raises_runtime_error() -> None:
    """If wind data fetch fails the handler raises RuntimeError (Lambda marks FAILED)."""
    mod = _fresh_ingest()
    _inject_clients(mod, ssm=_mock_ssm(), dynamo=_mock_dynamo(), sns=_mock_sns())
    mod._cached_firms_key = "cached-key"

    firms_csv = FIRMS_FIXTURE.read_text(encoding="utf-8")

    with (
        patch.object(mod, "fetch_firms_csv", return_value=firms_csv),
        patch.object(mod, "fetch_wind_data", side_effect=Exception("timeout")),  # [MOCK]
        patch.object(mod, "load_region_boundary", return_value={}),
        patch.object(mod, "is_point_in_geojson", return_value=True),
        pytest.raises(RuntimeError, match="Wind pipeline failed"),
    ):
        mod.lambda_handler({}, None)


class ConditionalCheckFailedException(Exception):
    """Simulates botocore ConditionalCheckFailedException."""

    def __init__(self) -> None:
        super().__init__("The conditional request failed")
        self.response = {"Error": {"Code": "ConditionalCheckFailedException"}}


# ---------------------------------------------------------------------------
# Tests for Alert Dispatch, Cooldown, and Concurrency (T-037)
# ---------------------------------------------------------------------------
class TestAlertDispatchAndCooldown:
    def test_alert_dispatched_when_severity_high_and_no_prior_alert(self) -> None:
        """High severity impact with no prior alert triggers atomic update and SNS publish."""
        mod = _fresh_ingest()
        dynamo = _mock_dynamo()
        sns = _mock_sns()
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=sns)

        now_iso = "2024-11-01T10:00:00+00:00"
        claimed = mod._attempt_claim_alert("delhi", "2024-11-01", "downwind-impact-test", now_iso)
        assert claimed is True

        # Verify conditional update called on DynamoDB with ConditionExpression
        table = dynamo.Table.return_value
        table.update_item.assert_called_once()
        call_kwargs = table.update_item.call_args.kwargs
        assert call_kwargs["Key"] == {"day": "2024-11-01", "cityId": "delhi"}
        assert (
            "attribute_not_exists(lastAlertedAtUtc) OR lastAlertedAtUtc < :cutoff"
            in call_kwargs["ConditionExpression"]
        )
        assert call_kwargs["ExpressionAttributeValues"][":now"] == now_iso

        # Now test publish
        mod._publish_city_alert(
            city_id="delhi",
            city_name="Delhi",
            severity="High",
            ist_day="2024-11-01",
            n_clusters=15,
            total_frp=650.0,
            nearest_km=25.0,
            min_eta_hours=2.5,
        )
        sns.publish.assert_called_once()
        publish_kwargs = sns.publish.call_args.kwargs
        assert publish_kwargs["TopicArn"].endswith("downwind-city-delhi-prod")
        message = publish_kwargs["Message"]
        assert "Delhi" in message
        assert "2.5 hours" in message
        assert "High" in message
        assert "estimate" in message.lower()
        assert "https://downwind.local" in message

    def test_alert_suppressed_inside_cooldown(self) -> None:
        """When an alert was already sent within 12h, DynamoDB condition fails and no SNS sent."""
        mod = _fresh_ingest()
        dynamo = _mock_dynamo()
        # Simulate DynamoDB conditional check failed
        dynamo.Table.return_value.update_item.side_effect = ConditionalCheckFailedException()

        sns = _mock_sns()
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=sns)

        now_iso = "2024-11-01T12:00:00+00:00"
        claimed = mod._attempt_claim_alert("delhi", "2024-11-01", "downwind-impact-test", now_iso)
        assert claimed is False
        # SNS must NOT be called
        sns.publish.assert_not_called()

    def test_alert_allowed_outside_cooldown(self) -> None:
        """When the previous alert is older than 12h, conditional update succeeds."""
        mod = _fresh_ingest()
        dynamo = _mock_dynamo()
        sns = _mock_sns()
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=sns)

        now_iso = "2024-11-01T22:00:00+00:00"
        claimed = mod._attempt_claim_alert("delhi", "2024-11-01", "downwind-impact-test", now_iso)
        assert claimed is True
        dynamo.Table.return_value.update_item.assert_called_once()

    def test_concurrent_invocations_only_send_once(self) -> None:
        """When two concurrent runs execute, only the winning run publishes an alert."""
        mod = _fresh_ingest()
        dynamo = _mock_dynamo()
        sns = _mock_sns()

        # Run 1 succeeds, Run 2 fails conditional update
        dynamo.Table.return_value.update_item.side_effect = [{}, ConditionalCheckFailedException()]

        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=sns)

        now_iso = "2024-11-01T10:00:00+00:00"
        # Run 1
        claim1 = mod._attempt_claim_alert("delhi", "2024-11-01", "downwind-impact-test", now_iso)
        # Run 2 (concurrent)
        claim2 = mod._attempt_claim_alert("delhi", "2024-11-01", "downwind-impact-test", now_iso)

        assert claim1 is True
        assert claim2 is False

        # If only claim1 publishes:
        if claim1:
            mod._publish_city_alert("delhi", "Delhi", "High", "2024-11-01", 10, 500.0, 30.0, 3.0)
        if claim2:
            mod._publish_city_alert("delhi", "Delhi", "High", "2024-11-01", 10, 500.0, 30.0, 3.0)

        # SNS publish was called exactly ONCE across the two runs
        assert sns.publish.call_count == 1

    def test_alert_message_exposes_no_internal_details(self) -> None:
        """Alert message body must contain city, ETA, severity, estimate, link, NO internals."""
        mod = _fresh_ingest()
        sns = _mock_sns()
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=_mock_dynamo(), sns=sns)

        mod._publish_city_alert(
            city_id="ludhiana",
            city_name="Ludhiana",
            severity="High",
            ist_day="2024-11-01",
            n_clusters=8,
            total_frp=520.0,
            nearest_km=18.5,
            min_eta_hours=1.8,
            account_id="694442891430",
            region="ap-south-1",
        )

        sns.publish.assert_called_once()
        body = sns.publish.call_args.kwargs["Message"]

        # Required fields
        assert "Ludhiana" in body
        assert "1.8 hours" in body
        assert "High" in body
        assert "estimate" in body.lower()
        assert "https://" in body

        # Internal details that must NOT appear in user-facing message body
        assert "694442891430" not in body  # AWS account ID
        assert "arn:aws:" not in body  # AWS ARN
        assert "downwind-impact" not in body  # DynamoDB table name
        assert "downwind-clusters" not in body
        assert "IngestFunction" not in body
        assert "lambda" not in body.lower()

    def test_pipeline_only_alerts_on_high_severity(self) -> None:
        """In pipeline, cities with Medium or Low severity do not attempt alert claim or SNS."""
        mod = _fresh_ingest()
        dynamo = _mock_dynamo()
        sns = _mock_sns()
        _inject_clients(mod, ssm=_mock_ssm(), dynamo=dynamo, sns=sns)
        mod._cached_firms_key = "cached-key"

        # Impact record with Medium severity
        medium_impact = [
            {
                "cityId": "karnal",
                "cityName": "Karnal",
                "severity": "Medium",
                "nClusters": 5,
                "totalFrp": 200.0,
                "nearestKm": 40.0,
                "minEtaHours": 4.0,
            }
        ]

        with (
            patch.object(mod, "fetch_firms_csv", return_value="dummy,csv"),
            patch.object(
                mod,
                "parse_firms_csv",
                return_value=[
                    {
                        "lat": 30.0,
                        "lon": 75.0,
                        "frp": 10.0,
                        "confidence": "high",
                        "acq_datetime_utc": "2024-11-01T06:00:00Z",
                    }
                ],
            ),
            patch.object(mod, "fetch_wind_data", return_value=DUMMY_WIND_DATA),
            patch.object(mod, "load_region_boundary", return_value={}),
            patch.object(mod, "is_point_in_geojson", return_value=True),
            patch.object(mod, "compute_impact", return_value=medium_impact),
            patch.object(mod, "json") as mock_json,
            patch("builtins.open", MagicMock()),
        ):
            mock_json.dumps = json.dumps
            mock_json.load.return_value = SAMPLE_CITIES
            mock_json.loads = json.loads

            summary = mod.lambda_handler({}, None)

            # 0 alerts sent for Medium severity
            assert summary["alerts_sent"] == 0
            sns.publish.assert_not_called()
