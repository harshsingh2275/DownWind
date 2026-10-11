"""Lambda handler dispatcher for DownWind.

SAM CodeUri points at the backend/ directory and the global Handler is
'handler.lambda_handler'. This module routes invocations to the correct
sub-handler based on the event source.

  - EventBridge scheduled events  → ingest.lambda_handler
  - API Gateway HTTP events        → api.lambda_handler

Real implementation comes in T-031 (ingest) and T-033 (api).
"""

from __future__ import annotations

from typing import Any


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Top-level dispatcher; routes to ingest or API handler based on event shape."""
    # API Gateway HTTP API events have a "requestContext" with "http" sub-key
    if "requestContext" in event and "http" in event.get("requestContext", {}):
        from src.handlers.api import lambda_handler as api_handler

        return api_handler(event, context)

    # EventBridge scheduled events, manual CLI invocations, or empty test events -> ingest
    if (
        event.get("source") == "aws.events"
        or event.get("action") == "manual"
        or not event
        or "requestContext" not in event
    ):
        from src.handlers.ingest import lambda_handler as ingest_handler

        return ingest_handler(event, context)

    # Unknown event source — log and return a 400-equivalent for safety
    return {
        "statusCode": 400,
        "body": '{"error": {"code": "UNKNOWN_EVENT", "message": "Unrecognised event source"}}',
    }
