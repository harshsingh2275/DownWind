"""API Lambda handler stub for DownWind (T-030 scaffold).

Full implementation in T-033:
  GET  /cities       — cities list from static JSON
  GET  /clusters     — DynamoDB clusters for window= or day=
  GET  /impact       — DynamoDB impact for window= or day=
  GET  /advisory     — static advisory JSON, lang=en|hi
  GET  /report       — district-wise aggregation
  POST /subscribe    — SNS per-city topic subscribe (double opt-in)

Error shape: {"error": {"code": "...", "message": "..."}}
"""

from __future__ import annotations

from typing import Any


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """HTTP API handler — stub pending T-033."""
    # TODO T-033: implement full API handler with routing, validation, DynamoDB queries
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "API handler not yet implemented (T-033)"}',
    }
