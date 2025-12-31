from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.schemas.envelopes import EnvelopeAccepted, EnvelopeError, EnvelopeReportMeta, Error
from app.schemas.reports import ReportExportRequest
from app.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["Reports"])

_svc: Optional[ReportsService] = None


def _get_service() -> ReportsService:
    if _svc is None:
        raise RuntimeError("ReportsService not initialized.")
    return _svc


# PUBLIC_INTERFACE
def set_reports_service(service: ReportsService) -> None:
    """Attach the ReportsService singleton used by this router."""
    global _svc
    _svc = service


@router.get(
    "/latest",
    response_model=EnvelopeReportMeta,
    responses={404: {"model": EnvelopeError}},
    operation_id="getLatestReport",
    summary="Get latest report metadata",
    description="Return latest report metadata for a given testRunId.",
)
def get_latest_report(
    testRunId: UUID = Query(..., description="Test run id (UUID) to fetch latest report for."),
) -> EnvelopeReportMeta:
    """Get latest report metadata.

    Args:
        testRunId: Test run id (UUID).

    Returns:
        EnvelopeReportMeta: OK envelope with ReportMeta.
    """
    try:
        report = _get_service().get_latest(testRunId)
        return EnvelopeReportMeta(status="ok", data=report)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=EnvelopeError(
                status="error",
                error=Error(code="not_found", message="No report found for test run.", details={"test_run_id": str(testRunId)}),
            ).model_dump(),
        )


@router.post(
    "/export",
    response_model=EnvelopeAccepted,
    responses={400: {"model": EnvelopeError}},
    operation_id="postReportsExport",
    summary="Queue report export",
    description="Queue report export for a test run, returning export_id and state=queued.",
)
def export_report(req: ReportExportRequest) -> EnvelopeAccepted:
    """Queue a report export.

    Args:
        req: ReportExportRequest body.

    Returns:
        EnvelopeAccepted: OK envelope with Accepted payload.
    """
    if not req.formats:
        raise HTTPException(
            status_code=400,
            detail=EnvelopeError(
                status="error",
                error=Error(code="bad_request", message="formats must contain at least one item.", details={"field": "formats"}),
            ).model_dump(),
        )
    accepted = _get_service().export(req)
    return EnvelopeAccepted(status="ok", data=accepted)


@router.get(
    "/download/{id}",
    response_class=PlainTextResponse,
    operation_id="getReportDownloadPlaceholder",
    summary="Download report (placeholder)",
    description="Placeholder download endpoint for generated download_url values (returns plain text).",
)
def download_report_placeholder(id: UUID) -> str:
    """Placeholder report download endpoint.

    In this bootstrap, reports are not actually generated as files. This endpoint exists
    so the `download_url` returned from /v1/reports/latest is a valid URL.

    Args:
        id: Report id (UUID).

    Returns:
        Plain text placeholder content.
    """
    return f"Report download placeholder for report_id={id}\n"
