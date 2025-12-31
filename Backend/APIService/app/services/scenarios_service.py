from __future__ import annotations

from typing import List
from uuid import UUID, uuid4

from app.schemas.envelopes import now_utc
from app.schemas.scenarios import Scenario, ScenarioCreateRequest, ScenarioUpdateRequest, ScenarioVersion
from app.repositories.scenarios_repository import ScenariosRepository


class ScenariosService:
    """Service for scenario CRUD and versioning (in-memory simulation)."""

    def __init__(self, repo: ScenariosRepository) -> None:
        self._repo = repo

    # PUBLIC_INTERFACE
    def list(self) -> List[Scenario]:
        """List all scenarios."""
        return self._repo.list()

    # PUBLIC_INTERFACE
    def create(self, req: ScenarioCreateRequest) -> Scenario:
        """Create a new scenario."""
        scenario = Scenario(
            id=uuid4(),
            name=req.name,
            version=1,
            type=req.type,
            params=req.params,
            tags=req.tags,
            description=req.description,
            created_at=now_utc(),
        )
        self._repo.create(scenario)
        return scenario

    # PUBLIC_INTERFACE
    def get(self, scenario_id: UUID) -> Scenario:
        """Get a scenario by id."""
        scenario = self._repo.get(scenario_id)
        if scenario is None:
            raise KeyError("scenario_not_found")
        return scenario

    # PUBLIC_INTERFACE
    def patch(self, scenario_id: UUID, req: ScenarioUpdateRequest) -> ScenarioVersion:
        """Patch a scenario, returning id + new version (versioned update)."""
        scenario = self._repo.get(scenario_id)
        if scenario is None:
            raise KeyError("scenario_not_found")

        updated = Scenario(
            id=scenario.id,
            name=req.name if req.name is not None else scenario.name,
            version=scenario.version + 1,
            type=scenario.type,
            params=req.params if req.params is not None else scenario.params,
            tags=req.tags if req.tags is not None else scenario.tags,
            description=scenario.description,
            created_at=scenario.created_at,
        )
        self._repo.update(scenario_id, updated)
        return ScenarioVersion(id=scenario_id, version=updated.version)
