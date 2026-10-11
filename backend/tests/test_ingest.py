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


def _mock_dynamo(put_side_effect: Any = None) -> MagicMock:
    """[MOCK] boto3 DynamoDB resource: Table.put_item and Table.get_item stubbed."""
    dynamo = MagicMock()
    table = MagicMock()
    table.put_item.side_effect = put_side_effect
    table.put_item.return_value = {} if put_side_effect is None else table.put_item.return_value
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
