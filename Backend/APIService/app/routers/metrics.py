from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.schemas.envelopes import EnvelopeCurrentMetrics
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

_metrics_service: MetricsService | None = None


def _get_metrics_service() -> MetricsService:
    # Avoid FastAPI dependency injection for now; a single service instance is attached at startup.
    if _metrics_service is None:
        raise RuntimeError("MetricsService not initialized. Did startup event run?")
    return _metrics_service


# PUBLIC_INTERFACE
def set_metrics_service(service: MetricsService) -> None:
    """Attach the MetricsService singleton used by this router."""
    global _metrics_service
    _metrics_service = service


@router.get(
    "/current",
    response_model=EnvelopeCurrentMetrics,
    operation_id="getCurrentMetrics",
    summary="Get current aggregated metrics",
    description="Returns the most recent aggregated Rx/Tx/Loss/Error metrics snapshot.",
)
def get_current_metrics(
    response: Response,
    testRunId: Optional[UUID] = Query(default=None, description="Optional test run id (UUID)."),
    includePerStream: bool = Query(default=False, description="Whether to include per-stream breakdown."),
) -> EnvelopeCurrentMetrics:
    """Get current metrics snapshot.

    Adds ETag/Last-Modified headers derived from snapshot timestamp + sequence.

    Args:
        response: FastAPI response object for setting headers.
        testRunId: Optional test run ID to scope the returned metrics.
        includePerStream: Whether per-stream metrics should be included.

    Returns:
        EnvelopeCurrentMetrics: OK envelope with CurrentMetrics payload.
    """
    service = _get_metrics_service()
    metrics = service.get_current_metrics(test_run_id=testRunId, include_per_stream=includePerStream)

    # ETag: stable across identical snapshot values; uses timestamp+sequence.
    # Weak ETag is sufficient since payload may include floating point rounding.
    etag = f'W/"{int(metrics.ts.timestamp())}-{metrics.sequence}"'
    response.headers["ETag"] = etag
    response.headers["Last-Modified"] = metrics.ts.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return EnvelopeCurrentMetrics(status="ok", data=metrics)
