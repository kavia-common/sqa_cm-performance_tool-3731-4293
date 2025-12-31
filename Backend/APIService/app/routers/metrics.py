from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query

from app.schemas.envelopes import EnvelopeCurrentMetrics
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

_metrics_service = MetricsService()


@router.get(
    "/current",
    response_model=EnvelopeCurrentMetrics,
    operation_id="getCurrentMetrics",
    summary="Get current aggregated metrics",
    description="Returns the most recent aggregated Rx/Tx/Loss/Error metrics snapshot.",
)
def get_current_metrics(
    testRunId: Optional[UUID] = Query(default=None, description="Optional test run id (UUID)."),
    includePerStream: bool = Query(default=False, description="Whether to include per-stream breakdown."),
) -> EnvelopeCurrentMetrics:
    """Get current metrics snapshot (placeholder implementation).

    Args:
        testRunId: Optional test run ID to scope the returned metrics.
        includePerStream: Whether per-stream metrics should be included.

    Returns:
        EnvelopeCurrentMetrics: OK envelope with CurrentMetrics payload.
    """
    metrics = _metrics_service.get_current_metrics(test_run_id=testRunId, include_per_stream=includePerStream)
    return EnvelopeCurrentMetrics(status="ok", data=metrics)
