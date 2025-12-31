from __future__ import annotations

import time

from fastapi import APIRouter

from app.schemas.envelopes import EnvelopeHealth, EnvelopeReady, HealthData, ReadyData

router = APIRouter(tags=["Health"])

_PROCESS_START = time.monotonic()
_VERSION = "1.0.0"


@router.get(
    "/health",
    response_model=EnvelopeHealth,
    operation_id="getHealth",
    summary="Health check",
    description="Liveness endpoint. Returns basic dependency health (placeholder).",
)
def get_health() -> EnvelopeHealth:
    """Liveness/health endpoint.

    Returns:
        EnvelopeHealth: OK envelope with uptime and dependency health state.
    """
    uptime_s = time.monotonic() - _PROCESS_START

    # Placeholder: dependencies are assumed ok for bootstrapping.
    data = HealthData(uptime_s=uptime_s, version=_VERSION, db="ok", xena="degraded")
    return EnvelopeHealth(status="ok", data=data)


@router.get(
    "/ready",
    response_model=EnvelopeReady,
    operation_id="getReady",
    summary="Readiness check",
    description="Readiness endpoint. Returns whether the service is ready to serve requests (placeholder).",
)
def get_ready() -> EnvelopeReady:
    """Readiness endpoint.

    Returns:
        EnvelopeReady: OK envelope indicating readiness.
    """
    # Placeholder readiness: always ready once process is up.
    return EnvelopeReady(status="ok", data=ReadyData(ready=True))
