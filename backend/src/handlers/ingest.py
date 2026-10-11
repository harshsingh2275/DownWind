"""Ingest Lambda handler stub for DownWind (T-030 scaffold).

Full implementation in T-031:
  - Read FIRMS MAP_KEY from SSM Parameter Store (cached across warm invocations).
  - Run the full pipeline: fetch → filter → region → cluster → wind → impact.
  - Write cluster and impact records to DynamoDB (idempotent PutItem).
  - Publish SNS alerts for high-severity cities that have passed the cooldown.
  - Structured logs, no secrets in log output.
"""

from __future__ import annotations

from typing import Any


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Ingest pipeline handler — stub pending T-031."""
    # TODO T-031: implement full ingest pipeline
    return {"status": "stub", "message": "Ingest handler not yet implemented (T-031)"}
