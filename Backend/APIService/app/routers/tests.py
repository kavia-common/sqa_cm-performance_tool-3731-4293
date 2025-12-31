from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.envelopes import EnvelopeError, EnvelopeTestStartAccepted, EnvelopeTestStatus, EnvelopeTestStopAccepted, Error
from app.schemas.tests import TestStartRequest, TestStopRequest
from app.services.tests_service import TestsService

router = APIRouter(prefix="/tests", tags=["Tests"])

_tests_service: Optional[TestsService] = None


def _get_service() -> TestsService:
    if _tests_service is None:
        raise RuntimeError("TestsService not initialized.")
    return _tests_service


# PUBLIC_INTERFACE
def set_tests_service(service: TestsService) -> None:
    """Attach the TestsService singleton used by this router."""
    global _tests_service
    _tests_service = service


@router.post(
    "/start",
    response_model=EnvelopeTestStartAccepted,
    responses={400: {"model": EnvelopeError}},
    operation_id="postTestsStart",
    summary="Start a test run",
    description="Accept a start request and return a test_run_id with state=starting.",
)
def start_test(req: TestStartRequest) -> EnvelopeTestStartAccepted:
    """Start a test run.

    Args:
        req: TestStartRequest body.

    Returns:
        EnvelopeTestStartAccepted: OK envelope with TestStartAccepted payload.
    """
    try:
        accepted = _get_service().start(req)
        return EnvelopeTestStartAccepted(status="ok", data=accepted)
    except Exception as e:
        # Validation errors are handled by FastAPI/Pydantic; this is for internal issues.
        raise HTTPException(
            status_code=400,
            detail=EnvelopeError(status="error", error=Error(code="bad_request", message=str(e), details=None)).model_dump(),
        )


@router.post(
    "/stop",
    response_model=EnvelopeTestStopAccepted,
    responses={400: {"model": EnvelopeError}, 404: {"model": EnvelopeError}},
    operation_id="postTestsStop",
    summary="Stop a test run",
    description="Accept a stop request and return test_run_id with state=stopping.",
)
def stop_test(req: TestStopRequest) -> EnvelopeTestStopAccepted:
    """Stop a test run.

    Args:
        req: TestStopRequest body.

    Returns:
        EnvelopeTestStopAccepted: OK envelope with TestStopAccepted payload.
    """
    try:
        accepted = _get_service().stop(req)
        return EnvelopeTestStopAccepted(status="ok", data=accepted)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=EnvelopeError(
                status="error",
                error=Error(code="not_found", message="Test run not found.", details={"test_run_id": str(req.test_run_id)}),
            ).model_dump(),
        )


@router.get(
    "/{id}",
    response_model=EnvelopeTestStatus,
    responses={404: {"model": EnvelopeError}},
    operation_id="getTestById",
    summary="Get test run status",
    description="Return current status (pending|running|completed|failed) with timestamps and optional reason.",
)
def get_test_status(id: UUID) -> EnvelopeTestStatus:
    """Get a test run status.

    Args:
        id: Test run id (UUID).

    Returns:
        EnvelopeTestStatus: OK envelope with TestStatus payload.
    """
    try:
        status = _get_service().get_status(id)
        return EnvelopeTestStatus(status="ok", data=status)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=EnvelopeError(
                status="error",
                error=Error(code="not_found", message="Test run not found.", details={"id": str(id)}),
            ).model_dump(),
        )
