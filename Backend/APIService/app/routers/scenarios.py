from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.envelopes import (
    EnvelopeError,
    EnvelopeScenario,
    EnvelopeScenarioList,
    EnvelopeScenarioVersion,
    Error,
)
from app.schemas.scenarios import ScenarioCreateRequest, ScenarioUpdateRequest
from app.services.scenarios_service import ScenariosService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

_svc: Optional[ScenariosService] = None


def _get_service() -> ScenariosService:
    if _svc is None:
        raise RuntimeError("ScenariosService not initialized.")
    return _svc


# PUBLIC_INTERFACE
def set_scenarios_service(service: ScenariosService) -> None:
    """Attach the ScenariosService singleton used by this router."""
    global _svc
    _svc = service


@router.get(
    "",
    response_model=EnvelopeScenarioList,
    operation_id="getScenarios",
    summary="List scenarios",
    description="Return all scenarios.",
)
def list_scenarios() -> EnvelopeScenarioList:
    """List scenarios.

    Returns:
        EnvelopeScenarioList: OK envelope with list of Scenario objects.
    """
    items = _get_service().list()
    return EnvelopeScenarioList(status="ok", data=items)


@router.post(
    "",
    response_model=EnvelopeScenario,
    responses={400: {"model": EnvelopeError}},
    operation_id="postScenarios",
    summary="Create scenario",
    description="Create a new scenario and return it.",
)
def create_scenario(req: ScenarioCreateRequest) -> EnvelopeScenario:
    """Create a scenario.

    Args:
        req: ScenarioCreateRequest body.

    Returns:
        EnvelopeScenario: OK envelope with created Scenario.
    """
    scenario = _get_service().create(req)
    return EnvelopeScenario(status="ok", data=scenario)


@router.get(
    "/{id}",
    response_model=EnvelopeScenario,
    responses={404: {"model": EnvelopeError}},
    operation_id="getScenarioById",
    summary="Get scenario",
    description="Return a scenario by id.",
)
def get_scenario(id: UUID) -> EnvelopeScenario:
    """Get a scenario by id.

    Args:
        id: Scenario id (UUID).

    Returns:
        EnvelopeScenario: OK envelope with Scenario payload.
    """
    try:
        scenario = _get_service().get(id)
        return EnvelopeScenario(status="ok", data=scenario)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=EnvelopeError(
                status="error",
                error=Error(code="not_found", message="Scenario not found.", details={"id": str(id)}),
            ).model_dump(),
        )


@router.patch(
    "/{id}",
    response_model=EnvelopeScenarioVersion,
    responses={400: {"model": EnvelopeError}, 404: {"model": EnvelopeError}},
    operation_id="patchScenarioById",
    summary="Update scenario (versioned)",
    description="Patch a scenario and return id + new version.",
)
def patch_scenario(id: UUID, req: ScenarioUpdateRequest) -> EnvelopeScenarioVersion:
    """Patch a scenario by id (creates a new version).

    Args:
        id: Scenario id (UUID).
        req: ScenarioUpdateRequest body.

    Returns:
        EnvelopeScenarioVersion: OK envelope with ScenarioVersion payload.
    """
    try:
        version = _get_service().patch(id, req)
        return EnvelopeScenarioVersion(status="ok", data=version)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=EnvelopeError(
                status="error",
                error=Error(code="not_found", message="Scenario not found.", details={"id": str(id)}),
            ).model_dump(),
        )
